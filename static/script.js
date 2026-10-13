document.addEventListener("DOMContentLoaded", function() {
    
    // Fetch and render Monthly Sales Chart
    fetch('/api/monthly_sales')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.month);
            const revenues = data.map(item => item.revenue);
            
            new Chart(document.getElementById('monthlySalesChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: revenues,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.2)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: { responsive: true }
            });
        });

    // Fetch and render Category Sales Chart
    fetch('/api/category_sales')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.category);
            const revenues = data.map(item => item.revenue);
            
            new Chart(document.getElementById('categorySalesChart'), {
                type: 'pie',
                data: {
                    labels: labels,
                    datasets: [{
                        data: revenues,
                        backgroundColor: ['#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#34495e', '#1abc9c']
                    }]
                },
                options: { responsive: true }
            });
        });

    // Fetch and render Top Products Chart
    fetch('/api/top_products')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.product_name);
            const revenues = data.map(item => item.revenue);
            
            new Chart(document.getElementById('topProductsChart'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: revenues,
                        backgroundColor: '#1abc9c'
                    }]
                },
                options: { responsive: true }
            });
        });

    // Fetch and render Supplier Performance Chart
    fetch('/api/supplier_performance')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.supplier_name);
            const revenues = data.map(item => item.revenue);
            
            new Chart(document.getElementById('supplierChart'), {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Revenue (₹)',
                        data: revenues,
                        backgroundColor: '#9b59b6'
                    }]
                },
                options: { 
                    responsive: true,
                    indexAxis: 'y'
                }
            });
        });

    // Fetch and render Order Status Chart
    fetch('/api/order_status')
        .then(response => response.json())
        .then(data => {
            const labels = data.map(item => item.order_status);
            const counts = data.map(item => item.count);
            
            new Chart(document.getElementById('orderStatusChart'), {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: counts,
                        backgroundColor: ['#2ecc71', '#f39c12', '#e74c3c', '#3498db']
                    }]
                },
                options: { responsive: true }
            });
        });
});
