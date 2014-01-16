/*
    naarad.js
*/
var colorSets = [
    ["#1F78B4", "#B2DF8A", "#A6CEE3"],
    ["#993399", "#B3CDE3", "#CCEBC5"],
    null
]

function plot(selector_id, div_id, colorset_id, advanced_source)
{
    var chart_data_selector = document.getElementById(selector_id);
    var chart_data_source = "";
    var chart_data_title = "" ;
    if(advanced_source) {
        chart_data_source = document.getElementById(selector_id).value;
        if(chart_data_source == ""){
            return;
        }
        var source = chart_data_source.split("/");
        chart_data_title = source[source.length-1];
    } else {
        chart_data_source = chart_data_selector.options[chart_data_selector.selectedIndex].value;
        chart_data_title = chart_data_selector.options[chart_data_selector.selectedIndex].text;
    }

    var div_width = document.getElementById(div_id).clientWidth;
    var div_height = document.getElementById(div_id).clientHeight;
    chart_1 = new Dygraph(document.getElementById(div_id), chart_data_source,
    {
        axes : {
            x : {
                ticker: Dygraph.dateTicker
            },
            y : {
                drawGrid: true
            }
        },
        legend: 'always',
        xValueParser: function(x) {
            var date_components = x.split(/[^0-9]/);
            return new Date(date_components[0], date_components[1]-1, date_components[2], date_components[3], date_components[4], date_components[5], date_components[6] || 0).getTime();
        },
        xlabel: "Time",
        colors: colorSets[colorset_id],
        labels: [ "Time", chart_data_title],
        labelsDiv: "labels-" + div_id
    }
    );
    chart_1.resize(div_width, window.screen.height*0.75/2)
}

function show_advanced_options()
{
    document.getElementById("txtDataSource2").value=""
    document.getElementById("advanced-options-div").hidden=false;
    document.getElementById("btnAdvanced").setAttribute( "onClick", "javascript: hide_advanced_options();" );
}

function hide_advanced_options()
{
    document.getElementById("txtDataSource2").value=""
    document.getElementById("select-chart-2").innerHTML = document.getElementById("select-chart-1").innerHTML;
    document.getElementById("advanced-options-div").hidden=true;
    document.getElementById("btnAdvanced").setAttribute( "onClick", "javascript: show_advanced_options();" );
}

function update_secondary_data_source_list()
{
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if(xhr.readyState == xhr.DONE && xhr.responseText != "" ) {
            files_list = xhr.responseText.split(",");
            console.log(files_list.toString());
            document.getElementById("select-chart-2").innerHTML = "";
            for(i=0; i< files_list.length ; i++) {
                console.log(files_list[i]);
                var opt = document.createElement("option");
                opt.style.background = "yellow";
                opt.value = document.getElementById("txtDataSource2").value + '/' + files_list[i] + '.csv';
                opt.innerHTML = files_list[i];
                document.getElementById("select-chart-2").add(opt,null);
            }
        }
    }
    xhr.open("GET",document.getElementById("txtDataSource2").value + "/list.txt", true);
    xhr.send(null);
}

function grading_rule_1(cellContent) {
    if ( cellContent > 0 ) {
       return "naarad-grader-pass";
    } else if (cellContent < 0 ) {
        return "naarad-grader-fail";
    }
    return "";
}

function grading_rule_2(cellContent) {
    if ( cellContent < 0 ) {
        return "naarad-grader-pass";
    } else if (cellContent > 0 ) {
        return "naarad-grader-fail";
    }
    return "";
}

function grade(tableID, cell_grading_rule)
{
    var tableRows = document.getElementById(tableID).getElementsByTagName("tr");
    for (var row=0; row < tableRows.length ; row++)
    {
        var cells = tableRows[row].getElementsByTagName("td");
        for (var cell=0; cell < cells.length ; cell++)
        {
            if (cells[cell].getAttribute("type") == "naarad-diff-td-percentage")
            {
                var cellContent = parseFloat(cells[cell].innerHTML);
                cells[cell].setAttribute("class",cell_grading_rule(cellContent));
            }
        }
    }
}

function switch_diff_table(metric)
{
    display_choice = document.getElementById("radio-diff-" + metric).checked;
    if (display_choice) {
        document.getElementById("table-diff-percent-" + metric).hidden = false;
        document.getElementById("table-diff-absolute-" + metric).hidden = true;
    } else {
        document.getElementById("table-diff-percent-" + metric).hidden = true;
        document.getElementById("table-diff-absolute-" + metric).hidden = false;
    }
}