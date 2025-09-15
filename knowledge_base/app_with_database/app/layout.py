from dash import html, dcc, dash_table


def make_app_layout():
    return html.Div(
        [
            html.H1("Holiday Request Manager", className="main-title"),
            html.P(
                "Review, approve, or decline holiday requests from your team.",
                className="subtitle",
            ),
            dash_table.DataTable(
                id="holiday-table",
                columns=[
                    {"name": "Request ID", "id": "request_id"},
                    {"name": "Employee", "id": "employee_name"},
                    {"name": "Start Date", "id": "start_date"},
                    {"name": "End Date", "id": "end_date"},
                    {"name": "Status", "id": "status"},
                    {"name": "Manager Comment", "id": "manager_note"},
                ],
                data=[],
                row_selectable="single",
                style_table={
                    "margin": "24px 0",
                    "width": "100%",
                    "borderRadius": "8px",
                    "overflow": "hidden",
                },
                style_cell={
                    "textAlign": "center",
                    "fontFamily": "Lato, Arial, sans-serif",
                    "fontSize": "1rem",
                },
                style_header={
                    "backgroundColor": "#1B5162",
                    "color": "white",
                    "fontWeight": "bold",
                    "fontSize": "1.05rem",
                },
                style_data_conditional=[
                    {
                        "if": {"filter_query": '{status} = "Approved"'},
                        "backgroundColor": "#d4edda",
                        "color": "#155724",
                    },
                    {
                        "if": {"filter_query": '{status} = "Declined"'},
                        "backgroundColor": "#f8d7da",
                        "color": "#721c24",
                    },
                ],
            ),
            html.Div(
                [
                    html.H3("Action", className="section-title"),
                    dcc.RadioItems(
                        id="action-radio",
                        options=[
                            {"label": "Approve", "value": "Approved"},
                            {"label": "Decline", "value": "Declined"},
                        ],
                        className="action-radio",
                    ),
                    dcc.Textarea(
                        id="manager-comment",
                        placeholder="Add a comment (optional)...",
                        className="manager-comment",
                    ),
                    html.Button(
                        "Submit", id="submit-action", n_clicks=0, className="submit-btn"
                    ),
                    html.Div(id="action-feedback", className="feedback"),
                ],
                className="action-panel",
            ),
            dcc.Interval(id="refresh-interval", interval=10 * 1000, n_intervals=0),
        ],
        className="container",
    )
