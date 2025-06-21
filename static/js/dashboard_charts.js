document.addEventListener('DOMContentLoaded', function () {
    // Line Chart: Sales Over Last 6 Months
    const ctxSales = document.getElementById('salesChart');
    if (ctxSales) {
        new Chart(ctxSales, {
            type: 'line',
            data: {
                labels: chartLabels,
                datasets: [{
                    label: 'Monthly Sales',
                    data: chartData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Sales Over the Last 6 Months'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return 'AED ' + value;
                            }
                        }
                    }
                }
            }
        });
    }

    // Doughnut Chart: Money Breakdown by Invoice Status
    const ctxStatus = document.getElementById('statusChart');
    if (ctxStatus) {
        new Chart(ctxStatus, {
            type: 'doughnut',
            data: {
                labels: statusLabels,
                datasets: [{
                    label: 'Invoice Status Breakdown',
                    data: statusData,
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.7)',   // Paid
                        'rgba(255, 99, 132, 0.7)',   // Unpaid
                        'rgba(255, 206, 86, 0.7)'    // Open
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(255, 99, 132, 1)',
                        'rgba(255, 206, 86, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    title: {
                        display: true,
                        text: 'Money Breakdown by Status'
                    }
                }
            }
        });
    }
});
