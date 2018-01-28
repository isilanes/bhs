var ctx = document.getElementById('item_chart').getContext('2d');
Chart.defaults.global.elements.line.fill = false;
Chart.defaults.global.legend.display = true;
Chart.defaults.global.animation.duration = 500;

$(document).ready(function() {
    var dataUrl = $('#data-url').attr("data-name");
    $.get(dataUrl, function(data) {
        dataset = {
            label: data.label,
            borderColor: data.color,
            data: data.data,
        }
        chart.data.datasets.push(dataset)

        chart.update()
    });
});

var chart = new Chart(ctx, {
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
                        unit: "month",
                        displayFormats: {
                            minute: "YYYY-MM-DD hh:mm:ss",
                            hour: "YYYY-MM-DD hh:mm",
                            day: "YYYY-MM-DD",
                            week: "YYYY-MM-DD",
                            month: "YYYY/MM"
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
                        labelString: "Euros",
                    }
                }
            ]
        }
    }
});
