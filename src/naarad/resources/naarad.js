var chartsList = [];
var timeseriesChartsList = [];
var cdfChartsList = [];
var chartIndex = 0;
var syncRange;
var colorSets = [
["#1F78B4", "#B2DF8A", "#A6CEE3"],
["#993399", "#B3CDE3", "#CCEBC5"],
null
];

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

function plot(selector_id, reset_selector_id, div_id, colorset_id, advanced_source, url_div)
{
  document.getElementById(reset_selector_id).selectedIndex=0;
  var chartIndex = parseInt(selector_id.split("-")[2]);
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
      for (var i = 0; i < timeseriesChartsList.length; i++)
      {
        if (timeseriesChartsList[i] == me) continue;
        if (timeseriesChartsList[i] != null)
        {
            timeseriesChartsList[i].updateOptions({
                dateWindow: syncRange
            });
        }
      }
    update_share_url();
    blockRedraw = false;
    }
  }
  );
  chart_1.resize(div_width, window.screen.height*0.75/2);
  chartsList[chartIndex] = chart_1;
  timeseriesChartsList[chartIndex] = chart_1;
  cdfChartsList[chartIndex] = null;
  update_share_url();
}

function plot_cdf(selector_id, reset_selector_id, div_id, colorset_id, advanced_source, url_div)
{
  document.getElementById(reset_selector_id).selectedIndex=0;
  var chartIndex = parseInt(selector_id.split("-")[2]);
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
  chartsList[chartIndex] = chart_1;
  cdfChartsList[chartIndex] = chart_1;
  timeseriesChartsList[chartIndex] = null;
  update_share_url();
}

function add_chart(container_div)
{
  var chartDiv = document.createElement("div");
  var template_div = "chart-div-0";
  var labelChartingDiv = "labels-charting-div-";
  var chartingDiv = "charting-div-";
  var innerHTMLContent = document.getElementById(template_div).innerHTML;
  chartIndex++;
  var newInnerHTMLContent = innerHTMLContent.replace(/-0/g, "-" + chartIndex.toString());
  chartDiv.className = "content";
  chartDiv.setAttribute("id","chart-div-" + chartIndex.toString());
  chartDiv.innerHTML = newInnerHTMLContent;
  document.getElementById(container_div).appendChild(chartDiv);
  document.getElementById(labelChartingDiv + chartIndex.toString()).innerHTML="";
  document.getElementById(chartingDiv + chartIndex.toString()).innerHTML="";
}

function remove_chart(chart_div, chart)
{
  var current_chart_div = document.getElementById(chart_div);
  current_chart_div.parentNode.removeChild(current_chart_div);
  var index = timeseriesChartsList.indexOf(chart);
  timeseriesChartsList.splice(index, 1);
}

function update_share_url()
{
    document.getElementById("text-share-report-url").value = save_chart_state();
}

function save_chart_state()
{
  if (chartsList.length == 0)
  {
      return window.location.toString();
  }
  var chartState = window.location.toString().split("?")[0] + "?charts=";
  for(var i=0; i<chartsList.length; i++)
  {
        chartState += chartsList[i].file_ + "," ;
  } 
  chartState = chartState.replace(/,$/,"");
  chartState += "&range=" + syncRange ;
  return chartState;
}

function load_saved_chart()
{
  var urlComponents = window.location.toString().split(/[?&]/);
  var charts = [];
  var range = [];
  for(var i=1; i < urlComponents.length; i++)
  {
    if(urlComponents[i].indexOf("charts=") >= 0 )
    {
      charts = urlComponents[i].split(/[=,]/);
    } else if(urlComponents[i].indexOf("range=") >= 0 )
    {
      range = urlComponents[i].split(/[=,]/);
      if (range.length == 3)
      {
        syncRange = [parseFloat(range[1]),parseFloat(range[2])];
      }
    }
  }
  for(var i=1;i<charts.length;i++)
  {
    if(i>1)
    {
      add_chart('chart-parent-div');
    }
    if(charts[i].indexOf("percentiles.csv") > 0)
    {
        selectDropdown('select-percentiles-' + (i-1), charts[i]);
        plot_cdf('select-percentiles-' + (i-1),'select-chart-' + (i-1),'charting-div-' + (i-1),0,false,'csv-url-div-' + (i-1));
    } else
    {
        selectDropdown('select-chart-' + (i-1), charts[i]);
        plot('select-chart-' + (i-1),'select-percentiles-' + (i-1),'charting-div-' + (i-1),0,false,'csv-url-div-' + (i-1));
    }
  }
  update_share_url();
}

function selectDropdown(dropdownId, dropdownValue)
{
  var dropdown = document.getElementById(dropdownId);
  for(var i=0; i<dropdown.options.length; i++)
  {
    if(dropdown.options[i].value == dropdownValue)
    {
      dropdown.options[i].selected = true;
      return;
    }
  }
}
