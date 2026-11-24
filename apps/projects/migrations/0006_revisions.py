import importlib

from django.db import migrations

# Revisions to two write-ups: Opus Equi's second challenge becomes the custom pinball loss, and
# Enular's simple moving-average example becomes the strategies in the library's own examples.
# Each passage is only replaced where it is still word for word what the last migration wrote,
# so edits made in the admin are kept.
EARLIER = importlib.import_module("apps.projects.migrations.0005_write_ups")

REPLACEMENTS = {
    "opus-equi": [
        (
            """The scope was the other challenge. The original plan also included accuracy measures such as
MAE and RMSE, analysis of adverse weather patterns and a derivatives-pricing component. With nine
weeks to build it alone, the requirements were reprioritised using MoSCoW, protecting the
essential journey: import and clean the data, train a model, and produce a forecast with its
uncertainty.
""",
            """The second was the quantile model. The XGBoost forecasts are trained on the pinball loss,
written as a custom objective. For a quantile level τ, the loss weights a forecast that falls
short by τ and one that overshoots by 1 − τ, so minimising it gives the τ-quantile of the
price rather than its mean. XGBoost builds each tree from the gradient and Hessian of the
objective: the pinball loss has a piecewise-constant gradient and no useful second
derivative, so the objective supplies a unit Hessian.

One booster is trained for each quantile, at 5%, 50% and 95%. Each starts from the empirical
quantile of the training data as its base score, which steadies the first rounds, and the
trained boosters are kept in a map keyed by quantile. Because quantiles trained separately can
cross, the service enforces the order of the three predictions, so the lower bound never
exceeds the median and the median never exceeds the upper bound.
""",
        ),
    ],
    "enular": [
        (
            """For example, a crossover operation can signal when a 10-day moving average moves above a
50-day one. A second condition can check whether volume is above its recent average. An AND
operation combines the two, and an entry rule uses the result to decide whether to place a
simulated buy order, while an exit rule decides when to close the position.

""",
            """The library's main example chains these together. A crossover operation compares the MACD
line with the Acceleration/Deceleration oscillator, an XOR gate combines that signal with a
second one, and an AND strategy operation turns the result into orders.

A second example trades several assets at once from a stochastic oscillator. It opens a long
position when the fast and slow lines are both below 20 and momentum is rising, and a short
position when both are above 80. Each trade is a bracket order: a limit entry 0.5% from the
close, a 3% stop-loss and a 6% take-profit, valid for ten days.

""",
        ),
    ],
}

OPUS_STACK = (
    "C#, .NET 8, WPF, Python, FastAPI, XGBoost, scikit-learn, pandas, NumPy, OxyPlot",
    "C#, .NET 8, WPF, Python, FastAPI, XGBoost, scikit-learn, pandas, NumPy, statsmodels, OxyPlot",
)


def revise(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    for project in Project.objects.filter(slug__in=REPLACEMENTS):
        body = project.body
        for old, new in REPLACEMENTS[project.slug]:
            body = body.replace(old, new)
        fields = []
        if body != project.body:
            project.body = body
            fields.append("body")
        if project.slug == "opus-equi" and project.stack == OPUS_STACK[0]:
            project.stack = OPUS_STACK[1]
            fields.append("stack")
        if fields:
            project.save(update_fields=fields)


class Migration(migrations.Migration):
    dependencies = [("projects", "0005_write_ups")]

    # Going back leaves the text as it is: nothing here is needed for the site to work.
    operations = [migrations.RunPython(revise, migrations.RunPython.noop)]
