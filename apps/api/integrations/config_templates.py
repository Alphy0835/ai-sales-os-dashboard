"""Default IntegrationSource.config_json templates for Django Admin."""

GOOGLE_SHEETS_CONFIG_TEMPLATE = {
    "provider": "google_sheets",
    "spreadsheet_id": "",
    "sheet_name": "Leads",
    "header_map": {
        "lead_id": "lead_id",
        "client_name": "client_name",
        "phone": "phone",
        "city": "city",
        "communication_comment": "communication_comment",
        "manager_email": "manager_email",
        "supervisor_email": "supervisor_email",
        "pipeline_stage": "pipeline_stage",
        "status_stage": "status_stage",
        "recording_url": "recording_url",
        "needs_review": "needs_review",
    },
    "skip_status_stages": ["done", "closed", "закрыт"],
    "review_rules": {
        "empty_comment_on_active": True,
        "auto_review_statuses": [],
    },
    "crm_vocabulary": {
        "stages": {
            "Closing": ["closing", "дожатие", "на дожатии"],
        },
        "statuses": {
            "Assigned": ["assigned", "назначен"],
            "open": ["open", "в работе"],
        },
    },
}
