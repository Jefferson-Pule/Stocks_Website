//create Tabulator on DOM element with id "example-table"

const csrf = document.getElementsByName('csrfmiddlewaretoken')[0].value
var tabledata = JSON.parse(document.currentScript.nextElementSibling.textContent);

console.log("table", tabledata);


if (typeof tabledata != 'string') {
    var data_subs = JSON.parse(tabledata.data_subs);
    var data_no_subs = JSON.parse(tabledata.data_no_subs);
    tabledata = data_subs.concat(data_no_subs)
};



var chartFormatter = function (cell, formatterParams, onRendered) {
    var content = document.createElement("span");
    var values = cell.getValue();
    
    //invert values if needed
    if (formatterParams.invert) {
        values = values.map(val => val * -1);
    }

    //setup chart options
    var options = {
        width: 145,
    }

    if (formatterParams.type == 'line') {
        console.log(values[values.length - 1])
        color = values[values.length - 1]
        maxi = values[values.length - 2]
        mini = values[values.length - 3]

        options.max = maxi
        options.min = mini

        values = values.slice(0, -3)
        if (color == 1) {
            options.fill = "#a4f595"
            options.stroke = "#26ba13"
        } else if (color == -1) {
            options.fill = "#f58989"
            options.stroke = "#e30e0e"
        } else {
            options.fill = "#c6d9fd"
            options.stroke = "#4d89f9"
        }

        
    }

    //add values to chart and style
    content.classList.add(formatterParams.type);
    content.innerHTML = values.join(",");


    if (formatterParams.fill) {
        options.fill = formatterParams.fill
    }



    //instantiate peity chart after the cell element has been aded to the DOM
    onRendered(function () {
        peity(content, formatterParams.type, options);
    });

    return content;
};

var buttomFormatter = function (cell, formatterParams, onRendered) { //plain text value
    var value = cell.getValue();
    if (value == 1) {
        return '<button type="button" class="btn btn-success">Subscribed</button>';
    } else {
        return '<button type="button" class="btn btn-secondary">Unsubscribed</button>';
    };

    return '<button type="button" class="btn btn-success">Success</button>';
};
//window.location.pathname

if (window.location.pathname[9] == "d") {
    //Table Constructor
    var example_table_sparkline = new Tabulator("#example-table", {
        maxHeight: "330px",
        minHeight: "75px",
        layout: "fitColumns",
        placeholder: "No Subscriptions",
        data: tabledata,
        movableRows: true,

        columns: [
            { rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 45, minWidth: 45 },
            {
                title: "Symbol", field: "Symbol", headerFilter: "input",
                formatter: "link",
                formatterParams: {
                    urlPrefix: `${window.location.protocol}//${window.location.hostname}:${window.location.port}/account/dashboard/`,
                    labelField: "Symbol"
                }
            },
            { title: "Name", field: "Name", headerFilter: "input" },
            { title: "Open", field: "Open", formatter: "money", formatterParams: {} },
            { title: "High", field: "High", formatter: "money", formatterParams: {} },
            { title: "Close", field: "Close", formatter: "money", formatterParams: {} },
            { title: "Low", field: "Low", formatter: "money", formatterParams: {} },
            { title: "Volume", field: "Volume" },
            //{ title: "Adj_Close", field: "Adj_Close", formatter: "money", formatterParams: {} },
            {
                title: "Line Chart", field: "line", formatter: chartFormatter, formatterParams: { type: "line" },},
            {
                title: "Subscribe", field: "User_subscribed", formatter: buttomFormatter, width: 135, minWidth: 135, align: "center", cellClick: function (e, cell) {
                    var symbol = cell.getRow().getCell('Symbol').getValue();
                    var action = cell.getValue();

                    if (action == 1) {
                        console.log(symbol, "Delete Subscription")
                    } else {
                        console.log(symbol, "Create Subscrition")
                    };

                    $.ajax({
                        type: 'POST',
                        url: 'explore',
                        data: {
                            'csrfmiddlewaretoken': csrf,
                            'symbol': symbol,
                            'action': action
                        },
                        success: (res) => {
                            console.log(res)
                        },
                        error: (err) => {
                            console.log(err)
                        }
                    });

                    if (action == 1) {

                        cell.setValue(0, true);

                    } else {

                        cell.setValue(1, true);

                    };

                }
            }
        ],
    });

    example_table_sparkline.on("rowMoved", function (row) {
        console.log("Row: " + row.getData().name + " has been moved");
    });

} else {
    //Table Constructor
    var example_table_sparkline = new Tabulator("#example-table", {
        maxHeight: '812px',
        minHeight: "75px",
        layout: "fitColumns",
        placeholder: "No Subscriptions",
        data: tabledata,
        movableRows: true,

        columns: [
            { rowHandle: true, formatter: "handle", headerSort: false, frozen: true, width: 45, minWidth: 45 },
            {
                title: "Symbol", field: "Symbol", headerFilter: "input",
                formatter: "link",
                formatterParams: {
                    urlPrefix: `${window.location.protocol}//${window.location.hostname}:${window.location.port}/account/dashboard/`,
                    labelField: "Symbol"
                }
            },
            { title: "Name", field: "Name", headerFilter: "input" },
            { title: "Open", field: "Open", formatter: "money", formatterParams: {} },
            { title: "High", field: "High", formatter: "money", formatterParams: {} },
            { title: "Close", field: "Close", formatter: "money", formatterParams: {} },
            { title: "Low", field: "Low", formatter: "money", formatterParams: {} },
            { title: "Volume", field: "Volume" },
            //{ title: "Adj_Close", field: "Adj_Close", formatter: "money", formatterParams: {} },
            { title: "Line Chart", field: "line", formatter: chartFormatter, formatterParams: { type: "line" } },
            {
                title: "Subscribe", field: "User_subscribed", formatter: buttomFormatter, width: 135, minWidth: 135, align: "center", cellClick: function (e, cell) {
                    var symbol = cell.getRow().getCell('Symbol').getValue();
                    var action = cell.getValue();

                    if (action == 1) {
                        console.log(symbol, "Delete Subscription")
                    } else {
                        console.log(symbol, "Create Subscrition")
                    };

                    $.ajax({
                        type: 'POST',
                        url: 'explore',
                        data: {
                            'csrfmiddlewaretoken': csrf,
                            'symbol': symbol,
                            'action': action
                        },
                        success: (res) => {
                            console.log(res)
                        },
                        error: (err) => {
                            console.log(err)
                        }
                    });

                    if (action == 1) {

                        cell.setValue(0, true);

                    } else {

                        cell.setValue(1, true);

                    };

                }
            }
        ],
    });

    example_table_sparkline.on("rowMoved", function (row) {
        console.log("Row: " + row.getData().name + " has been moved");
    });
}

