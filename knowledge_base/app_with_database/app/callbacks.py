from dash import Input, Output, State, callback_context
from lakebase_connector import get_holiday_requests, update_request_status
import pandas as pd


def register_callbacks(app):
    @app.callback(
        Output("holiday-table", "data"),
        [
            Input("refresh-interval", "n_intervals"),
            Input("submit-action", "n_clicks"),
            Input("action-feedback", "children"),
        ],
    )
    def refresh_table(n_intervals, n_clicks, action_feedback):
        holiday_request_df = get_holiday_requests()
        return holiday_request_df.to_dict("records")

    @app.callback(
        [
            Output("action-feedback", "children"),
            Output("action-radio", "value"),
            Output("manager-comment", "value"),
        ],
        Input("submit-action", "n_clicks"),
        State("holiday-table", "selected_rows"),
        State("holiday-table", "data"),
        State("action-radio", "value"),
        State("manager-comment", "value"),
        prevent_initial_call=True,
    )
    def submit_holiday_request_review(
        n_clicks, selected_row_nr, table_data, selected_action, manager_comment
    ):
        if (selected_action is None) | (selected_row_nr is None):
            return "Please select a request and approve/decline."
        row_idx = selected_row_nr[0]
        selected_row = table_data[row_idx]
        request_id = selected_row["request_id"]

        update_request_status(
            request_id=request_id, status=selected_action, comment=manager_comment
        )
        return f"You {selected_action.lower()} request {request_id}.", None, ""
