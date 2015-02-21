var chartsList = [];
var timeseriesChartsList = [];
var cdfChartsList = [];
var timeseriesOptionsList = [];
var cdfOptionsList = [] ;
var chartIndex = 0;
var syncRange;
var colorSets = [
["#1F78B4", "#B2DF8A", "#A6CEE3"],
["#993399", "#B3CDE3", "#CCEBC5"],
null
];
var resourcesPrefix = "resources/";
var resourcesSuffix = ".csv";

function switchDiffTable(metric)
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
    var chart_data_selector = document.getElementById(selector_id);
    var csvURL = chart_data_selector.options[chart_data_selector.selectedIndex].value;
    var xhr = new XMLHttpRequest();
    var anomaliesURL = csvURL.replace('.csv', '.anomalies.csv');
    var anomalies = [];
    var chartObject = timeseriesChartsList[chartIndex];
    xhr.onreadystatechange = function() {
        if(xhr.readyState == xhr.DONE) {
            anomalies = xhr.responseText.replace(/\n$/, '').split('\n');
            plotWithAnomalies(selector_id, reset_selector_id, div_id, colorset_id, advanced_source, url_div, anomalies);
        }
    }
    xhr.open('GET', anomaliesURL, true);
    xhr.send(null);
}

function plotWithAnomalies(selector_id, reset_selector_id, div_id, colorset_id, advanced_source, url_div, anomalies)
{
  document.getElementById(reset_selector_id).selectedIndex=0;
  var chartIndex = parseInt(selector_id.split("-")[2]);
  var chart_data_selector = document.getElementById(selector_id);
  var chart_data_source = "";
  var chart_data_title = "" ;
  chart_data_source = chart_data_selector.options[chart_data_selector.selectedIndex].value;
  chart_data_title = chart_data_selector.options[chart_data_selector.selectedIndex].text;
  document.getElementById(url_div).innerHTML = "<a href=\"javascript:convertCSVTimeStamp('" + chart_data_source + "');\" class=\"btn btn-primary btn-csv\" target=\"_blank\">Download CSV</a>"
  var div_width = document.getElementById(div_id).clientWidth;
  var div_height = document.getElementById(div_id).clientHeight;
  var blockRedraw = false;
  var initial = true;
  var chart_1 = new Dygraph(document.getElementById(div_id), chart_data_source,
  {
    height : window.screen.height*0.75/2,
    width : div_width,
    axes : {
      x : {
            ticker: Dygraph.dateTicker,
            axisLabelFormatter: function(x) {
                var date = new Date(x);
                return (makeTwoDigit(date.getHours()) + ":" + makeTwoDigit(date.getMinutes()) + ":" + makeTwoDigit(date.getSeconds()) + "." + date.getMilliseconds());
            },
            valueFormatter: function(x) {
                var date = new Date(x);
                return (makeTwoDigit(date.getMonth()+1) + "/" + makeTwoDigit(date.getDate()) + "/" + date.getFullYear() + " " + makeTwoDigit(date.getHours()) + ":" + makeTwoDigit(date.getMinutes()) + ":" + makeTwoDigit(date.getSeconds()) + "." + date.getMilliseconds());
            }
          },
      y : {
            drawGrid: true
          }
    },
    legend: 'always',
    xlabel: "Time",
    colors: colorSets[colorset_id],
    labels: [ "Time", chart_data_title],
    labelsDiv: "labels-" + div_id,
    dateWindow: syncRange,
    underlayCallback: function(canvas, area, chart_1) {
        for(var i=0; i<anomalies.length; i++)
        {
            var anomalyData = anomalies[i].split(",");
            var left = chart_1.toDomXCoord(parseInt(anomalyData[1]));
            var right = chart_1.toDomXCoord(parseInt(anomalyData[2]));
            if(left == right) {
                left = left - 1;
                right = right + 1;
            }
            canvas.fillStyle = 'lightblue';
            canvas.fillRect(left, area.y, right-left, area.h);
        }
    },
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
    updateShareUrl();
    blockRedraw = false;
    }
  }
  );
  chartsList[chartIndex] = chart_1;
  timeseriesChartsList[chartIndex] = chart_1;
  cdfChartsList[chartIndex] = null;
  updateShareUrl();
}

function plotCdf(selector_id, reset_selector_id, div_id, colorset_id, advanced_source, url_div)
{
  document.getElementById(reset_selector_id).selectedIndex=0;
  var chartIndex = parseInt(selector_id.split("-")[2]);
  var chart_data_selector = document.getElementById(selector_id);
  var chart_data_source = "";
  var chart_data_title = "" ;
  chart_data_source = chart_data_selector.options[chart_data_selector.selectedIndex].value;
  chart_data_title = chart_data_selector.options[chart_data_selector.selectedIndex].text;
  document.getElementById(url_div).innerHTML = "<a href=" + chart_data_source + " class=\"btn btn-primary btn-csv\" target=\"_blank\">Download CSV</a>"
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
  updateShareUrl();
}

function addChart(container_div)
{
  chartIndex++;

  var chartDiv = document.createElement("div");
  chartDiv.className = "content";
  chartDiv.setAttribute("id","chart-div-" + chartIndex.toString());

  var selectionDiv = document.createElement("div");
  selectionDiv.className = "row";
  selectionDiv.innerHTML = document.getElementById("selection-div-0").innerHTML.replace(/-0/g, "-" + chartIndex.toString());;
  chartDiv.appendChild(selectionDiv);

  var removeChartButton = document.createElement("button");
  removeChartButton.className = "btn btn-danger";
  removeChartButton.type = "button";
  var removeChartButtonText = document.createTextNode("-");
  removeChartButton.appendChild(removeChartButtonText);
  removeChartButton.setAttribute("onclick", "removeChart('chart-div-" + chartIndex.toString() + "'," + chartIndex.toString() + ")");

  var labelsChartingDiv = document.createElement("div");
  labelsChartingDiv.setAttribute("id","labels-charting-div-" + chartIndex.toString());
  labelsChartingDiv.setAttribute("class","chart-label");
  chartDiv.appendChild(labelsChartingDiv);

  var chartingDiv = document.createElement("div");
  chartingDiv.setAttribute("id","charting-div-" + chartIndex.toString());
  chartingDiv.setAttribute("class","chart-area");
  chartDiv.appendChild(chartingDiv);

  var csvURLDiv = document.createElement("div");
  csvURLDiv.setAttribute("id","csv-url-div-" + chartIndex.toString());
  csvURLDiv.setAttribute("class","chart-csv");
  chartDiv.appendChild(csvURLDiv);
  chartDiv.appendChild(document.createElement("hr"));

  document.getElementById(container_div).appendChild(chartDiv);
  document.getElementById("button-div-" + chartIndex.toString()).appendChild(removeChartButton);
  resetFilter('select-chart-' + chartIndex.toString(), 'select-percentiles-' + chartIndex.toString(), 'filter-text-' + chartIndex.toString());
}

function uploadFile()
{
    var formData = new FormData();
    var xhr = new XMLHttpRequest();
    for(var i = 0; i < document.getElementById("the-file").files.length; i++)
    {
        formData.append("file[]", document.getElementById("the-file").files[i]);
    }
    xhr.open("POST", "/analyze", true);
    xhr.send(formData);
    document.getElementById("the-file").value = "";
    document.getElementById("status-div").innerHTML = "Upload Complete. Request has been queued for analysis."
}

function removeChart(chart_div, index)
{
  var current_chart_div = document.getElementById(chart_div);
  current_chart_div.parentNode.removeChild(current_chart_div);
  timeseriesChartsList[index] = null;
  cdfChartsList[index] = null;
  chartsList[index] = null;
  updateShareUrl();
}

function updateShareUrl()
{
    document.getElementById("text-share-report-url").value = saveChartState();
}

function saveChartState()
{
  if (chartsList.length == 0)
  {
      return window.location.toString();
  }
  var chartState = window.location.toString().split("?")[0] + "?charts=";
  for(var i = 0; i < chartsList.length; i++)
  {
        if (chartsList[i] != null)
        {
           chartState += chartsList[i].file_ + "," ;
        }
  } 
  chartState = chartState.replace(/,$/,"");
  chartState += "&range=" + syncRange ;
  return chartState;
}

function getOptions()
{
  for(var i = 0; i < document.getElementById('select-chart-0').options.length; i++)
  {
    timeseriesOptionsList[i] = document.getElementById('select-chart-0').options[i].label;
  }
  for(var i = 0; i < document.getElementById('select-percentiles-0').options.length; i++)
  {
    cdfOptionsList[i] = document.getElementById('select-percentiles-0').options[i].label;
  }
}

function loadSavedChart()
{
  var urlComponents = window.location.toString().split(/[?&]/);
  var charts = [];
  var range = [];
  getOptions();
  for(var i = 1; i < urlComponents.length; i++)
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
  for(var i = 1; i < charts.length; i++)
  {
    if(i > 1)
    {
      addChart('chart-parent-div');
    }
    if(charts[i].indexOf("percentiles.csv") > 0)
    {
        selectDropdown('select-percentiles-' + (i-1), charts[i]);
        plotCdf('select-percentiles-' + (i-1),'select-chart-' + (i-1),'charting-div-' + (i-1),0,false,'csv-url-div-' + (i-1));
    } else
    {
        selectDropdown('select-chart-' + (i-1), charts[i]);
        plot('select-chart-' + (i-1),'select-percentiles-' + (i-1),'charting-div-' + (i-1),0,false,'csv-url-div-' + (i-1));
    }
  }
  updateShareUrl();
}

function selectDropdown(dropdownId, dropdownValue)
{
  var dropdown = document.getElementById(dropdownId);
  for(var i = 0; i < dropdown.options.length; i++)
  {
    if(dropdown.options[i].value == dropdownValue)
    {
      dropdown.options[i].selected = true;
      return;
    }
  }
}

function filter(timeseriesSelector, cdfSelector, filterId)
{
  var filteredTimeseriesList = [];
  var filteredCDFList = [];
  var filters = [];
  var filterText = document.getElementById(filterId).value.trim().replace(/[ ]+/," ");
  if(filterText.length > 0)
  {
    filters = filterText.split(" ");
    filteredTimeseriesList = filterList(filters,timeseriesOptionsList);
    if (filteredTimeseriesList.length > 1)
    {
      purgeOptions(timeseriesSelector);
      addOptions(timeseriesSelector, filteredTimeseriesList);
    }
    filteredCDFList = filterList(filters,cdfOptionsList);
    if (filteredCDFList.length > 1)
    {
      purgeOptions(cdfSelector);
      addOptions(cdfSelector, filteredCDFList);
    }
  }
}

function filterList(filters, list)
{
  var filteredList = [];
  filteredList[0] = list[0];
  for(var i = 1; i < list.length; i++)
  {
    for(var j = 0; j < filters.length; j++)
    {
      if(list[i].indexOf(filters[j]) > -1)
      {
        filteredList.push(list[i]);
        continue;
      }
    }
  }
  return filteredList; 
}

function getOptionElement(text)
{
  var option = document.createElement("option");
  option.text = text;
  option.value = resourcesPrefix + text + resourcesSuffix;
  return option
}


function purgeOptions(selectorId)
{
  var select = document.getElementById(selectorId);
  select.innerHTML = "";
}

function addOptions(selectorId, list)
{
  var select = document.getElementById(selectorId);
  for(var i = 0; i < list.length; i++)
  {
    select.add(getOptionElement(list[i]));
  }
}

function resetFilter(timeseriesSelector, cdfSelector, filterId)
{
  document.getElementById(filterId).value = "";
  purgeOptions(timeseriesSelector);
  addOptions(timeseriesSelector,timeseriesOptionsList);
  purgeOptions(cdfSelector);
  addOptions(cdfSelector,cdfOptionsList);
}

function convertCSVTimeStamp(csvURL)
{
    var xhr = new XMLHttpRequest();
    var csvData = '';
    var url = csvURL.split("/");
    var fileName = url[url.length - 1];
    xhr.onreadystatechange = function() {
        if(xhr.readyState == xhr.DONE) {
            var lines = xhr.responseText.split("\n");
            for(var i=0; i< lines.length; i++)
            {
                var lineData = lines[i].split(",");
                if(syncRange === undefined || (lineData[0] > syncRange[0] && lineData[0] < syncRange[1]))
                {
                    var date = new Date(parseInt(lineData[0]));
                    var timestamp = makeTwoDigit(date.getMonth()+1) + "/" + makeTwoDigit(date.getDate()) + "/" + date.getFullYear() + " " + makeTwoDigit(date.getHours()) + ":" + makeTwoDigit(date.getMinutes()) + ":" + makeTwoDigit(date.getSeconds()) + "." + date.getMilliseconds();
                    csvData += timestamp + ',' + lineData[1] + '\n';
                }
            }
            download(csvData,fileName, 'text/csv');
        }
    }
    xhr.open('GET', csvURL, true);
    xhr.send(null);
}

function download(content, filename, contentType)
{
    if(!contentType) contentType = 'application/octet-stream';
    if(navigator.userAgent.indexOf('Chrome') > -1)
    {
        var a = document.createElement('a');
        var blob = new Blob([content], {'type':contentType});
        a.href = window.URL.createObjectURL(blob);
        a.download = filename;
        a.click();
    } else {
        document.location = 'data:' + contentType + ',' + encodeURIComponent(content);
    }
}

function makeTwoDigit(input)
{
    return ("0" + input).slice(-2);
}

/**
 * jumpTo
 * This function given a target point allows for jumping to a given anchor location.
 * It should not have the hash in the target name.
 */
function jumpTo(target)
{
  window.location.hash = target;
}
