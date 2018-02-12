var ctx_nhosts = document.getElementById('item_chart_credit').getContext('2d');
Chart.defaults.global.elements.line.fill = false;
Chart.defaults.global.legend.display = true;
Chart.defaults.global.animation.duration = 500;

$(document).ready(function() {
    var dataUrl = $('#data-url-credit').attr("data-name");
    $.get(dataUrl, function(data) {

        // Windows:
        dataset = {
            label: "Windows",
            borderColor: "#ff0000",
            data: data.data.win,
        }
        chart_credit.data.datasets.push(dataset)

        // Linux:
        dataset = {
            label: "Linux",
            borderColor: "#00cc00",
            data: data.data.lin,
        }
        chart_credit.data.datasets.push(dataset)

        // MacOS:
        dataset = {
            label: "Darwin",
            borderColor: "#0000ff",
            data: data.data.mac,
        }
        chart_credit.data.datasets.push(dataset)

        // Other:
        dataset = {
            label: "Other",
            borderColor: "#00ccff",
            data: data.data.other,
        }
        chart_credit.data.datasets.push(dataset)

        chart_credit.update()
    });
});

var chart_credit = new Chart(ctx_nhosts, {
    // The type of chart we want to create:
    type: 'line',
    
    // The data for our dataset (begins empty):
    data: {
        datasets: []
    },
    
    // Configuration options go here:
    options: {
        scales: {
            xAxes: [
                {
                    type: "time",
                    position: 'bottom',
                    ticks: {
                        minRotation: 30
                    },
                    time: {
                        unit: "year",
                        displayFormats: {
                            minute: "YYYY-MM-DD hh:mm:ss",
                            hour: "YYYY-MM-DD hh:mm",
                            day: "YYYY-MM-DD",
                            week: "YYYY-MM-DD",
                            month: "YYYY/MM",
                            year: "YYYY",
                        }
                    },
                    scaleLabel: {
                        display: true,
                        labelString: "Fecha",
                    }
                }
            ],
            yAxes: [
                {
                    type: "linear",
                    position: 'left',
                    ticks: {
                        min: 0
                    },
                    scaleLabel: {
                        display: true,
                        labelString: "Credit",
                    }
                }
            ]
        }
    }
});
