from dash import Dash
from layout import make_app_layout
from callbacks import register_callbacks

app = Dash(__name__, title="Holiday Request Manager", suppress_callback_exceptions=True)
app.layout = make_app_layout()
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
