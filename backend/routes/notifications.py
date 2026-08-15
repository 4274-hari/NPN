from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Notification

notifications_bp = Blueprint("notifications", __name__)


def current_uid():
    return int(get_jwt_identity())


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    uid = current_uid()
    items = (
        Notification.query.filter_by(recipient_id=uid)
        .order_by(Notification.created_at.desc())
        .limit(50)
        .all()
    )
    return jsonify([n.to_dict() for n in items])


@notifications_bp.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    uid = current_uid()
    count = Notification.query.filter_by(recipient_id=uid, is_read=False).count()
    return jsonify({"count": count})


@notifications_bp.route("/read-all", methods=["POST"])
@jwt_required()
def read_all():
    uid = current_uid()
    Notification.query.filter_by(recipient_id=uid, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"success": True})


@notifications_bp.route("/<int:notif_id>/read", methods=["POST"])
@jwt_required()
def read_one(notif_id):
    uid = current_uid()
    n = Notification.query.filter_by(id=notif_id, recipient_id=uid).first_or_404()
    n.is_read = True
    db.session.commit()
    return jsonify(n.to_dict())
