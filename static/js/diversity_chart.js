var chartdata_d = JSON.parse(document.currentScript.nextElementSibling.textContent);

//console.log(chartdata_d)


var d_data = chartdata_d.data;

var d_labels = chartdata_d.labels;

const totalsum = d_data.reduce(
    (p_sum, i) => p_sum + i, 0
);

if (totalsum == 0) {
    totalsum=1
};

const ul = document.querySelector("#details ul");

const data_d = {
    labels: d_labels,
    datasets: [{
        label: 'My First Dataset',
        data: d_data,
        borderColor: [

            'rgba(51, 187, 238, 1)',
            'rgba(0, 153, 136, 1)',
            'rgba(238, 119, 51, 1)',
            'rgba(204, 51, 17, 1)',
            'rgba(238, 51, 119, 1)',
            'rgba(0, 119, 187, 1)',
            'rgba(187, 187, 187, 1)', //grey
            'rgba(0, 0, 0, 1)',   //black-for-white back
            'rgba(238, 119, 51, 1)',
            'rgba(204, 51, 17, 1)',
            'rgba(238, 51, 119, 1)'
        ],
        borderWidth: 1,

        backgroundColor: [

            'rgba(51, 187, 238, 1)',
            'rgba(0, 153, 136, 1)',
            'rgba(238, 119, 51, 1)',
            'rgba(204, 51, 17, 1)',
            'rgba(238, 51, 119, 1)',
            'rgba(0, 119, 187, 1)',
            'rgba(187, 187, 187, 1)', //grey
            'rgba(255, 255, 255, 1)',   //white
            'rgba(238, 119, 51, 1)',
            'rgba(204, 51, 17, 1)',
            'rgba(238, 51, 119, 1)'
        ],

        hoverOffset: 4
    }]
};

const config_d = {
    type: 'doughnut',
    data: data_d,
    options: {

        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                callbacks: {
                    label: (context) => {
                        const newLineArray = []
                        //console.log(context)
                        const perce = Math.round(context.parsed / totalsum * 100).toFixed(0)
                        newLineArray.push(`${context.parsed} stocks in sector`)
                        return newLineArray
                    }
                }
            },
        }
    }
};


// render init block

const myChart_d = new Chart(
    document.getElementById('diversity_chart'),
    config_d
);
myChart_d.options.plugins.legend.position = 'right';
myChart_d.update();

// Populate Legend

const populateUl = () => {
    //console.log(data_d.labels)
    data_d.labels.forEach((l, i) => {
        let li = document.createElement("li");
        li.innerHTML = `<span class='percentage' style='color:${data_d.datasets[0].borderColor[i]};'>${Math.round(data_d.datasets[0].data[i] / totalsum * 100).toFixed(0)}%</span> ${l} `;
        ul.appendChild(li);
    });
};
populateUl();


