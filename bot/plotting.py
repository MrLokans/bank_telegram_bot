import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

# add extra styling for our graphs
sns.set_style("darkgrid")


def reset_plot(plot=plt):
    """Resets all data on the given plot"""
    plot.clf()
    plot.cla()


# TODO: This function should be less specific
def render_exchange_rate_plot(x_axe, y_buy, y_sell, output_file):
    """Renders plot to the given file"""
    # Extra setup to correctly display dates on X-axis
    xtick_locator = mdates.AutoDateLocator()
    xtick_formatter = mdates.AutoDateFormatter(xtick_locator)

    plt.gca().xaxis.set_major_formatter(xtick_formatter)
    plt.gca().xaxis.set_major_locator(xtick_locator)
    plt.plot(x_axe, y_buy, label='Buy')
    plt.plot(x_axe, y_sell, label='Sell')
    plt.legend()
    plt.gcf().autofmt_xdate()

    plt.savefig(output_file)
    return plt


def generate_plot_name(bank_name, currency_name, start_date, end_date):
    if isinstance(start_date, datetime.date) or\
       isinstance(start_date, datetime.datetime):
        start_date = start_date.strftime("%d-%m-%Y")

    if isinstance(end_date, datetime.date) or\
       isinstance(end_date, datetime.datetime):
        end_date = end_date.strftime("%d-%m-%Y")

    name = "{}_{}_{}_{}.png".format(bank_name,
                                    currency_name,
                                    end_date,
                                    start_date)

    return name
