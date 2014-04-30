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

var chartsList = [];
var syncRange;
var colorSets = [
["#1F78B4", "#B2DF8A", "#A6CEE3"],
["#993399", "#B3CDE3", "#CCEBC5"],
null
];

function plot(selector_id, div_id, colorset_id, advanced_source, url_div)
{
  var chart_data_selector = document.getElementById(selector_id);
  var chart_data_source = "";
  var chart_data_title = "" ;
  chart_data_source = chart_data_selector.options[chart_data_selector.selectedIndex].value;
  chart_data_title = chart_data_selector.options[chart_data_selector.selectedIndex].text;
  document.getElementById(url_div).innerHTML = "<a href=" + chart_data_source + " target=\"_blank\">[csv]</a>"
  var div_width = document.getElementById(div_id).clientWidth;
  var div_height = document.getElementById(div_id).clientHeight;
  var blockRedraw = false;
  var initialized = false;
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
    labelsDiv: "labels-" + div_id,
    dateWindow: syncRange,
    drawCallback: function(me, initial) {
      if (blockRedraw || initial) return;
      blockRedraw = true;
      syncRange = me.xAxisRange();
      for (var i = 0; i < chartsList.length; i++)
      {
        if (chartsList[i] == me) continue;
        chartsList[i].updateOptions({
          dateWindow: syncRange
        });
      }
    blockRedraw = false;
    }
  }
  );
  chart_1.resize(div_width, window.screen.height*0.75/2);
  chartsList.push(chart_1);
}

function plot_cdf(selector_id, div_id, colorset_id, advanced_source, url_div)
{
  var chart_data_selector = document.getElementById(selector_id);
  var chart_data_source = "";
  var chart_data_title = "" ;
  chart_data_source = chart_data_selector.options[chart_data_selector.selectedIndex].value;
  chart_data_title = chart_data_selector.options[chart_data_selector.selectedIndex].text;
  document.getElementById(url_div).innerHTML = "<a href=" + chart_data_source + " target=\"_blank\">[csv]</a>"
  var div_width = document.getElementById(div_id).clientWidth;
  var div_height = document.getElementById(div_id).clientHeight;
  chart_1 = new Dygraph(document.getElementById(div_id), chart_data_source,
  {
    axes : {
      y : {
            drawGrid: true
          }
    },
    legend: 'always',
    xlabel: "Percentiles",
    colors: colorSets[colorset_id],
    labels: [ "Percentiles", chart_data_title],
    labelsDiv: "labels-" + div_id
  }
  );
  chart_1.resize(div_width, window.screen.height*0.75/2);
}

function add_chart(container_div)
{
  var chartDiv = document.createElement("div");
  var template_div = "chart-div-1";
  var labelChartingDiv = "labels-charting-div-";
  var chartingDiv = "charting-div-";
  var children = document.getElementById(container_div).childNodes;
  var count = children.length + 1;
  var innerHTMLContent = document.getElementById(template_div).innerHTML;
  var newInnerHTMLContent = innerHTMLContent.replace(/-1/g, "-" + count.toString());
  chartDiv.className = "content";
  chartDiv.setAttribute("id","chart-div-" + count.toString());
  chartDiv.innerHTML = newInnerHTMLContent;
  document.getElementById(container_div).appendChild(chartDiv);
  document.getElementById(labelChartingDiv + count.toString()).innerHTML="";
  document.getElementById(chartingDiv + count.toString()).innerHTML="";
}




