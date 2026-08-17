from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

from bson import ObjectId
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from config import settings
from database import close_mongo_connection, connect_to_mongo, get_database, get_social_database
from service.hybrid_classifier import hybrid_classify
from service.emoji_service import clean_text
from service.auth_service import new_session_token
from service.routing_service import TOPIC_TEAMS, route_topic_to_team
from service.rag_service import generate_reply


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    yield
    close_mongo_connection()


app = FastAPI(title="Nexora Customer Response API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    await get_database().command("ping")
    return {"status": "ok", "database": "connected"}



class MentionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=254)
    platform: str = Field(min_length=1, max_length=50)
    text: str = Field(min_length=1, max_length=5000)


class TweetRequest(MentionRequest):
    handle: str = Field(min_length=2, max_length=50)
    parent_tweet_id: str | None = None


class CompanyLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class SocialLoginRequest(BaseModel):
    identifier: str = Field(min_length=2, max_length=254)
    password: str


class ResponseUpdateRequest(BaseModel):
    response_text: str = Field(min_length=1, max_length=5000)
    action: str = Field(pattern="^(draft|approved)$")


class HumanReplyRequest(BaseModel):
    response_text: str = Field(min_length=1, max_length=5000)


def public_company_user(user: dict) -> dict:
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "role": user["role"], "team": user["team"]}


def public_social_user(user: dict) -> dict:
    return {"id": str(user["_id"]), "name": user["name"], "email": user["email"], "handle": user["handle"], "color": user.get("color", "green")}


async def current_company_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Company login is required")
    token = authorization.removeprefix("Bearer ")
    database = get_database()
    session = await database.company_sessions.find_one({"token": token, "expires_at": {"$gt": datetime.now(timezone.utc)}})
    if not session:
        raise HTTPException(status_code=401, detail="Your session has expired. Please log in again.")
    user = await database.company_users.find_one({"_id": session["company_user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="Company account no longer exists")
    return user


CompanyUser = Annotated[dict, Depends(current_company_user)]


def labels_from_classification(classification: dict) -> dict:
    labels = {}
    for item in classification["prediction"]:
        key = next(key for key in item if key != "score")
        labels[key] = item[key]
    return labels


async def process_company_mention(request: MentionRequest, social_tweet_id: ObjectId | None = None, conversation_memory: str = "") -> dict:
    """Company-side processing. This only writes to the company database."""
    database = get_database()
    now = datetime.now(timezone.utc)
    email = request.email.strip().lower()

    customer = await database.customers.find_one_and_update(
        {"email": email},
        {
            "$set": {
                "name": request.name.strip(),
                "platform": request.platform.strip(),
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    cleaned_text = clean_text(request.text)
    classification = hybrid_classify(cleaned_text)
    labels = labels_from_classification(classification)
    requires_human = classification["escalation"]["escalation"] is True or classification["escalation"]["escalation"] == "review"
    if requires_human:
        # Escalations deliberately bypass the LLM: the assigned team writes the response.
        generated_reply, generation_error = None, None
    else:
        try:
            generated_reply = generate_reply(cleaned_text, labels, conversation_memory)
            generation_error = None
        except Exception as error:
            generated_reply = None
            generation_error = str(error)
    mention = {
        "customer_id": customer["_id"],
        "source_tweet_id": social_tweet_id,
        "platform": request.platform.strip(),
        "company_tag": settings.company_tag,
        "original_text": request.text,
        "cleaned_text": cleaned_text,
        "classification": classification,
        "labels": labels,
        "status": "classified",
        "llm_response": generated_reply,
        "llm_generation_error": generation_error,
        "response_status": "pending",
        "created_at": now,
        "conversation_id": str(customer["_id"]),
    }
    saved_mention = await database.mentions.insert_one(mention)

    escalation = classification["escalation"]
    if requires_human:
        team = route_topic_to_team(labels["topic"])
        escalation_doc = {
            "mention_id": saved_mention.inserted_id,
            "team": team,
            "topic": labels["topic"],
            "priority": escalation["priority"],
            "reason": escalation["reason"],
            "status": "open",
            "created_at": now,
        }
        await database.escalations.insert_one(escalation_doc)
        await database.mentions.update_one({"_id": saved_mention.inserted_id}, {"$set": {"response_status": "escalated"}})
        await database.team_notifications.insert_one({
            "team": team,
            "type": "escalation",
            "mention_id": saved_mention.inserted_id,
            "message": f"New {escalation['priority']} escalation for {team}",
            "read": False,
            "created_at": now,
        })

    return {
        "message": "Mention saved and classified",
        "mention_id": str(saved_mention.inserted_id),
        "classification": classification,
    }


async def process_forwarded_tweet(payload: dict, tweet_id: str) -> None:
    """Run slower ML/RAG work after the public tweet has already been published."""
    social_database = get_social_database()
    try:
        social_tweet = await social_database.tweets.find_one({"_id": ObjectId(tweet_id)})
        memory_lines = []
        if social_tweet and social_tweet.get("parent_tweet_id"):
            thread_tweets = await social_database.tweets.find({"thread_root_id": social_tweet["thread_root_id"], "_id": {"$ne": ObjectId(tweet_id)}}).sort("created_at", 1).to_list(length=30)
            for thread_tweet in thread_tweets:
                memory_lines.append(f"Customer: {thread_tweet.get('text', '')}")
                if thread_tweet.get("company_reply"):
                    memory_lines.append(f"Nexora: {thread_tweet['company_reply'].get('text', '')}")
        result = await process_company_mention(TweetRequest(**payload), ObjectId(tweet_id), "\n".join(memory_lines))
        mention = await get_database().mentions.find_one({"_id": ObjectId(result["mention_id"])})
        status = "escalated" if mention and mention.get("response_status") == "escalated" else "ready"
        await social_database.tweets.update_one({"_id": ObjectId(tweet_id)}, {"$set": {
            "forwarded_to_company": True, "company_mention_id": result["mention_id"], "processing_status": status,
        }})
    except Exception as error:
        await social_database.tweets.update_one({"_id": ObjectId(tweet_id)}, {"$set": {"processing_status": "failed", "processing_error": str(error)}})


@app.post("/mentions")
async def process_mention(request: MentionRequest):
    """Direct company ingestion endpoint, kept for API testing."""
    if settings.company_tag.lower() not in request.text.lower():
        raise HTTPException(status_code=400, detail=f"Text must include the company tag: {settings.company_tag}")
    return await process_company_mention(request)


@app.post("/social/tweets")
async def create_social_tweet(request: TweetRequest, background_tasks: BackgroundTasks):
    """Social clone writes its tweet first; tagged tweets are forwarded to the company pipeline."""
    social_database = get_social_database()
    now = datetime.now(timezone.utc)
    parent_tweet_id = None
    thread_root_id = None
    is_company_mention = settings.company_tag.lower() in request.text.lower()
    if request.parent_tweet_id:
        if not ObjectId.is_valid(request.parent_tweet_id):
            raise HTTPException(status_code=400, detail="The tweet you are replying to no longer exists")
        parent = await social_database.tweets.find_one({"_id": ObjectId(request.parent_tweet_id)})
        if not parent:
            raise HTTPException(status_code=404, detail="The tweet you are replying to no longer exists")
        parent_tweet_id = parent["_id"]
        thread_root_id = parent.get("thread_root_id") or parent["_id"]
        is_company_mention = is_company_mention or bool(parent.get("company_reply"))
    tweet = {
        "author_email": request.email.strip().lower(), "author_handle": request.handle.strip(), "author_name": request.name.strip(),
        "text": request.text, "platform": request.platform, "created_at": now,
        "forwarded_to_company": False, "processing_status": "processing" if is_company_mention else None,
        "parent_tweet_id": parent_tweet_id, "thread_root_id": thread_root_id,
    }
    saved_tweet = await social_database.tweets.insert_one(tweet)
    if not thread_root_id:
        thread_root_id = saved_tweet.inserted_id
        await social_database.tweets.update_one({"_id": saved_tweet.inserted_id}, {"$set": {"thread_root_id": thread_root_id}})
    if not is_company_mention:
        return {"message": "Tweet published", "tweet_id": str(saved_tweet.inserted_id), "forwarded_to_company": False}
    background_tasks.add_task(process_forwarded_tweet, request.model_dump(), str(saved_tweet.inserted_id))
    return {"message": "Tweet published. Nexora is reviewing it.", "tweet_id": str(saved_tweet.inserted_id), "forwarded_to_company": True, "processing_status": "processing"}


@app.get("/social/tweets")
async def get_social_tweets():
    """Return social posts, including any company reply approved in the console."""
    social_database = get_social_database()
    tweets = await social_database.tweets.find().sort("created_at", -1).to_list(length=200)
    result = []
    for tweet in tweets:
        user = await social_database.social_users.find_one({"email": tweet["author_email"]})
        result.append({
            "id": str(tweet["_id"]),
            "author": public_social_user(user) if user else {"name": tweet.get("author_handle", "Unknown"), "email": tweet["author_email"], "handle": tweet.get("author_handle", "@unknown"), "color": "green"},
            "text": tweet["text"],
            "created_at": tweet["created_at"],
            "company_reply": tweet.get("company_reply"),
            "processing_status": tweet.get("processing_status"),
            "parent_tweet_id": str(tweet["parent_tweet_id"]) if tweet.get("parent_tweet_id") else None,
        })
    return {"tweets": result}


@app.post("/auth/social/login")
async def login_social_account(request: SocialLoginRequest):
    identifier = request.identifier.strip().lower()
    handle = f"@{identifier.removeprefix('@')}"
    user = await get_social_database().social_users.find_one({"$or": [{"email": identifier}, {"handle": handle}]})
    if not user or request.password != user.get("password"):
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")
    return {"user": public_social_user(user)}


async def create_company_session(user: dict) -> dict:
    database = get_database()
    token = new_session_token()
    await database.company_sessions.insert_one({
        "token": token, "company_user_id": user["_id"],
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=12),
        "created_at": datetime.now(timezone.utc),
    })
    return {"token": token, "user": public_company_user(user)}


@app.post("/auth/company/login")
async def login_company_account(request: CompanyLoginRequest):
    user = await get_database().company_users.find_one({"email": request.email.strip().lower()})
    if not user or request.password != user.get("password"):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return await create_company_session(user)


@app.get("/company/teams")
async def get_company_teams(_: CompanyUser):
    return {"teams": sorted(set(TOPIC_TEAMS.values()))}


@app.get("/company/complaints")
async def get_complaints(company_user: CompanyUser):
    database = get_database()
    query = {} if company_user["role"] == "admin" else {"labels.topic": {"$exists": True}}
    documents = await database.mentions.find(query).sort("created_at", -1).to_list(length=200)
    complaints = []
    for mention in documents:
        customer_id = mention.get("customer_id")
        social_user = await database.customers.find_one({"_id": customer_id}) if customer_id else None
        complaints.append({
            "id": str(mention["_id"]), "text": mention["original_text"], "platform": mention["platform"],
            "labels": mention.get("labels", {}), "status": mention["status"],
            "response_status": mention.get("response_status", "pending"),
            "created_at": mention.get("created_at"), "user_name": social_user["name"] if social_user else mention.get("author_name", "Unknown user"),
        })
    return {"complaints": complaints, "viewer": public_company_user(company_user)}


@app.get("/company/complaints/{mention_id}")
async def get_complaint_detail(mention_id: str, _: CompanyUser):
    if not ObjectId.is_valid(mention_id):
        raise HTTPException(status_code=404, detail="Complaint not found")
    database = get_database()
    mention = await database.mentions.find_one({"_id": ObjectId(mention_id)})
    if not mention:
        raise HTTPException(status_code=404, detail="Complaint not found")
    customer_id = mention.get("customer_id")
    social_user = await database.customers.find_one({"_id": customer_id}) if customer_id else None
    escalation = await database.escalations.find_one({"mention_id": mention["_id"]})
    history_documents = await database.mentions.find({"customer_id": mention.get("customer_id")}).sort("created_at", -1).to_list(length=8)
    conversation_history = [{"id": str(item["_id"]), "text": item.get("original_text", ""), "response": item.get("human_response") or item.get("llm_response")} for item in reversed(history_documents)]
    return {
        "id": str(mention["_id"]), "text": mention["original_text"], "cleaned_text": mention["cleaned_text"],
        "classification": mention["classification"], "labels": mention.get("labels", {}), "status": mention["status"],
        "response_status": mention.get("response_status", "pending"),
        "llm_response": None if escalation else mention.get("llm_response"),
        "human_response": mention.get("human_response"),
        "user": {"name": social_user["name"], "email": social_user["email"]} if social_user else {"name": mention.get("author_name", "Unknown user"), "email": mention.get("author_email")},
        "escalation": {"id": str(escalation["_id"]), "team": escalation["team"], "priority": escalation["priority"], "status": escalation["status"], "reason": escalation["reason"]} if escalation else None,
        "conversation_history": conversation_history,
    }


@app.patch("/company/complaints/{mention_id}/response")
async def save_company_response(mention_id: str, request: ResponseUpdateRequest, company_user: CompanyUser):
    if not ObjectId.is_valid(mention_id):
        raise HTTPException(status_code=404, detail="Complaint not found")
    if company_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only an admin can approve AI responses")
    escalation = await get_database().escalations.find_one({"mention_id": ObjectId(mention_id)})
    if escalation:
        raise HTTPException(status_code=409, detail="Escalated messages must be answered by the assigned team")
    response_status = "approved" if request.action == "approved" else "draft"
    result = await get_database().mentions.update_one({"_id": ObjectId(mention_id)}, {"$set": {
        "llm_response": request.response_text, "response_status": response_status,
        "responded_by": company_user["_id"], "responded_at": datetime.now(timezone.utc),
    }})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if response_status == "approved":
        mention = await get_database().mentions.find_one({"_id": ObjectId(mention_id)})
        source_tweet_id = mention.get("source_tweet_id") if mention else None
        if source_tweet_id:
            await get_social_database().tweets.update_one({"_id": source_tweet_id}, {"$set": {
                "company_reply": {
                    "text": request.response_text,
                    "author": company_user["name"],
                    "approved_at": datetime.now(timezone.utc),
                }
            }})
    return {"message": f"Response {response_status}", "response_status": response_status}


@app.get("/company/escalations")
async def get_escalations(company_user: CompanyUser):
    database = get_database()
    query = {} if company_user["role"] == "admin" else {"team": company_user["team"]}
    records = await database.escalations.find(query).sort("created_at", -1).to_list(length=200)
    result = []
    for escalation in records:
        mention = await database.mentions.find_one({"_id": escalation["mention_id"]})
        result.append({"id": str(escalation["_id"]), "mention_id": str(escalation["mention_id"]), "team": escalation["team"], "topic": escalation["topic"], "priority": escalation["priority"], "reason": escalation["reason"], "status": escalation["status"], "text": mention["original_text"] if mention else "Message unavailable", "human_response": mention.get("human_response") if mention else None})
    return {"escalations": result}


@app.get("/company/analytics")
async def get_analytics(company_user: CompanyUser):
    if company_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Analytics are available to admins only")
    database = get_database()

    async def grouped(field: str) -> dict:
        rows = await database.mentions.aggregate([{"$group": {"_id": f"$labels.{field}", "count": {"$sum": 1}}}]).to_list(length=50)
        return {str(row["_id"] or "unknown"): row["count"] for row in rows}

    return {
        "total_mentions": await database.mentions.count_documents({}),
        "open_escalations": await database.escalations.count_documents({"status": "open"}),
        "approved_responses": await database.mentions.count_documents({"response_status": "approved"}),
        "sentiment": await grouped("sentiment"), "topics": await grouped("topic"), "urgency": await grouped("urgency"),
        "daily_volume": [{"date": row["_id"], "count": row["count"]} for row in await database.mentions.aggregate([
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}}, "count": {"$sum": 1}}}, {"$sort": {"_id": -1}}, {"$limit": 14}, {"$sort": {"_id": 1}},
        ]).to_list(length=14)],
    }


@app.get("/company/team/inbox")
async def get_team_inbox(company_user: CompanyUser):
    if company_user["role"] == "admin":
        raise HTTPException(status_code=403, detail="Choose a team account to open its workspace")
    database = get_database()
    escalations = await database.escalations.find({"team": company_user["team"], "status": {"$in": ["open", "working"]}}).sort("created_at", -1).to_list(length=200)
    items = []
    for escalation in escalations:
        mention = await database.mentions.find_one({"_id": escalation["mention_id"]})
        customer = await database.customers.find_one({"_id": mention.get("customer_id")}) if mention else None
        items.append({"id": str(escalation["_id"]), "mention_id": str(escalation["mention_id"]), "customer": customer.get("name", "Customer") if customer else "Customer", "text": mention.get("original_text", "") if mention else "", "priority": escalation["priority"], "reason": escalation["reason"], "status": escalation["status"]})
    return {"items": items, "team": company_user["team"]}


@app.post("/company/escalations/{escalation_id}/reply")
async def reply_to_escalation(escalation_id: str, request: HumanReplyRequest, company_user: CompanyUser):
    if company_user["role"] == "admin" or not ObjectId.is_valid(escalation_id):
        raise HTTPException(status_code=403, detail="A team member must reply from their assigned workspace")
    database = get_database()
    escalation = await database.escalations.find_one({"_id": ObjectId(escalation_id), "team": company_user["team"]})
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found for your team")
    now = datetime.now(timezone.utc)
    mention = await database.mentions.find_one_and_update({"_id": escalation["mention_id"]}, {"$set": {"human_response": request.response_text, "response_status": "team_replied", "responded_by": company_user["_id"], "responded_at": now}}, return_document=ReturnDocument.AFTER)
    await database.escalations.update_one({"_id": escalation["_id"]}, {"$set": {"status": "resolved", "resolved_at": now, "responded_by": company_user["_id"]}})
    if mention and mention.get("source_tweet_id"):
        await get_social_database().tweets.update_one({"_id": mention["source_tweet_id"]}, {"$set": {"company_reply": {"text": request.response_text, "author": company_user["name"], "approved_at": now, "type": "team"}, "processing_status": "resolved"}})
    return {"message": "Human response sent and returned to the admin inbox"}
