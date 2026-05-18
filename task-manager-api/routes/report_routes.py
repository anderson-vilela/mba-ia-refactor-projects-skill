from flask import Blueprint

from controllers import category_controller, report_controller


report_bp = Blueprint("reports", __name__)

report_bp.add_url_rule(
    "/reports/summary", view_func=report_controller.summary_report, methods=["GET"]
)
report_bp.add_url_rule(
    "/reports/user/<int:user_id>",
    view_func=report_controller.user_report,
    methods=["GET"],
)
report_bp.add_url_rule(
    "/categories", view_func=category_controller.list_categories, methods=["GET"]
)
report_bp.add_url_rule(
    "/categories", view_func=category_controller.create_category, methods=["POST"]
)
report_bp.add_url_rule(
    "/categories/<int:cat_id>",
    view_func=category_controller.update_category,
    methods=["PUT"],
)
report_bp.add_url_rule(
    "/categories/<int:cat_id>",
    view_func=category_controller.delete_category,
    methods=["DELETE"],
)
