
new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Completed', 'Pending'],
        datasets: [{
            data: [{{ completed }}, {{ pending }}]
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false   
    }
});
