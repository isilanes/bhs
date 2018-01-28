# Extra libs:
import matplotlib
import matplotlib.pyplot as plt

# Config:
matplotlib.use("Agg")

# Classes:
class Plot(object):

    # Constructor:
    def __init__(self, ymax=None):
        self.ymax = ymax
        self.fns = {
            "index": None,
            "intake": None,
            "range": None,
        }

    # Public methods:
    def plot(self, Data=None, Style=None):
        """Plot data, as requested."""

        object_list = Data.objects.order_by("-timestamp")

        # Read log:
        x_axis, y_axes = [], []
        for object in object_list:
            x_axis.append(object.timestamp)
            for i, kw in enumerate(object.plottable_attributes()):
                value = float(getattr(object, kw))
                try:
                    y_axes[i].append(value)
                except:
                    y_axes.append([])
                    y_axes[i].append(value)

        # Plot data:
        plt.figure(figsize=(16,9), dpi=100)
        for i, (y_axis, kw) in enumerate(zip(y_axes, object.plottable_attributes())):
            try:
                title = Style.objects.get(name=kw).long_name
                style = Style.objects.get(name=kw).style
                objective = Style.objects.get(name=kw).objective
            except:
                title = "Unknown"
                style = "-"
                objective = 1
            c = {
                "objective": objective,
                "style": style,
                "title": title,
            }
            plt.plot(x_axis, [y/c["objective"] for y in y_axis], c["style"], label=c["title"])

        if self.ymax:
            plt.ylim([0, self.ymax])

        #xmin, xmax = plt.xlim()
        #plt.xlim(xmax=xmax+1) # add one day
        plt.legend(bbox_to_anchor=(1.00, 1), loc=2, borderaxespad=0.5)
        plt.subplots_adjust(left=0.05, right=0.80, top=0.95, bottom=0.10)
        plt.savefig(self.fns["index"])

    def plot_item(self, item, Data=None, Style=None):
        """Plot item data, as requested."""

        if item == "intake":
            self.plot_intake(Data, Style)

        elif item == "range":
            self.plot_range(Data, Style)

        elif item == "kms_per_year":
            self.plot_kms_per_year(Data, Style)

        elif item == "euros_per_month":
            self.plot_euros_per_month(Data, Style)

    def plot_intake(self, Data=None, Style=None):
        """Plot intake data, as requested."""

        data = Data.objects.order_by("timestamp")

        # Read log:
        x_axis = [d.total_kms for d in data[1:]]
        y_axis = [100*d.litres/d.partial_kms for d in data[1:]]

        # Plot data:
        plt.figure(figsize=(21, 8), dpi=100)
        title = "Litros a los 100 km"
        style = "ro:"
        plt.plot(x_axis, y_axis, style, label=title)

        if self.ymax:
            plt.ylim([0, self.ymax])

        plt.xlabel("kms")
        plt.ylabel(title)
        #plt.legend(bbox_to_anchor=(1.00, 1), loc=2, borderaxespad=0.5)
        plt.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.10)
        plt.savefig(self.fns["intake"])

    def plot_range(self, Data=None, Style=None):
        """Plot range data, as requested."""

        data = Data.objects.order_by("timestamp")

        # Read log:
        y_axis = [d.partial_kms for d in data[1:]]

        # Plot data:
        plt.figure(figsize=(21, 8), dpi=100)
        title = "km de automomía"
        style = "go--"
        plt.plot(y_axis, style, label=title)

        if self.ymax:
            plt.ylim([0, self.ymax])

        plt.xlabel("# repostaje")
        plt.ylabel(title)
        #plt.legend(bbox_to_anchor=(1.00, 1), loc=2, borderaxespad=0.5)
        plt.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.10)
        plt.savefig(self.fns["range"])

    def plot_kms_per_year(self, Data=None, Style=None):
        """Plot kms per year data, as requested."""

        data = Data.objects.order_by("timestamp")
        date0 = data[0].timestamp

        # Read log:
        x_axis = [d.timestamp for d in data[1:]]
        days = [(d.timestamp - date0).total_seconds()/86400. for d in data[1:]] # days
        y_axis = [365*d.total_kms/dt for d, dt in zip(data[1:], days)]

        # Plot data:
        plt.figure(figsize=(21, 8), dpi=100)
        title = "kms anuales"
        plt.plot(x_axis, y_axis, "bo:", label=title)

        if self.ymax:
            plt.ylim([0, self.ymax])

        plt.xlabel("fecha")
        plt.ylabel(title)
        #plt.legend(bbox_to_anchor=(1.00, 1), loc=2, borderaxespad=0.5)
        plt.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.10)
        plt.savefig(self.fns["kms_per_year"])

    def plot_euros_per_month(self, Data=None, Style=None):
        """Plot euros per month data, as requested."""

        data = Data.objects.order_by("timestamp")
        day0 = data[0].timestamp

        # Read log:
        x_axis = [d.timestamp for d in data[1:]]

        y_axis = []
        gastado = 0
        for datum in data[1:]:
            gastado += datum.litres * datum.price # euros gastados repostando
            epm = 30*86400*gastado/(datum.timestamp - day0).total_seconds()
            y_axis.append(epm)

        # Plot data:
        plt.figure(figsize=(21, 8), dpi=100)
        title = "euros mensuales"
        plt.plot(x_axis, y_axis, "bo:", label=title)

        if self.ymax:
            plt.ylim([0, self.ymax])

        plt.xlabel("fecha")
        plt.ylabel(title)
        #plt.legend(bbox_to_anchor=(1.00, 1), loc=2, borderaxespad=0.5)
        plt.subplots_adjust(left=0.05, right=0.90, top=0.95, bottom=0.10)
        plt.savefig(self.fns["euros_per_month"])

