// sparkline.js — trend sparklines + history fetching for Nora's fund dashboard
// Provides: sparkline(), fetchFundHistory(), loadAllTrends(), injectSparklines()

function sparkline(values, w, h, isUp) {
  if (!values || values.length < 2) return '';
  var min = Math.min.apply(null, values);
  var max = Math.max.apply(null, values);
  var range = max - min || 1;
  var pad = 3, pts = '';
  for (var i = 0; i < values.length; i++) {
    var x = pad + (i / (values.length - 1)) * (w - 2 * pad);
    var y = pad + (1 - (values[i] - min) / range) * (h - 2 * pad);
    pts += x.toFixed(1) + ',' + y.toFixed(1) + ' ';
  }
  var color = isUp ? 'var(--red)' : 'var(--green)';
  var lastX = pad + w - 2*pad;
  var lastY = pad + (1 - (values[values.length-1] - min) / range) * (h - 2*pad);
  return '<svg width="' + w + '" height="' + h + '" style="display:inline-block;vertical-align:middle">'
    + '<polyline points="' + pts.trim() + '" fill="none" stroke="' + color + '" stroke-width="1.2" '
    + 'stroke-linecap="round" stroke-linejoin="round" opacity="0.6"/>'
    + '<circle cx="' + lastX.toFixed(1) + '" cy="' + lastY.toFixed(1) + '" r="2" fill="' + color + '" opacity="0.85"/>'
    + '</svg>';
}

async function fetchFundHistory(code) {
  var key = 'navhist_' + code;
  var cached = localStorage.getItem(key);
  if (cached) {
    try { var d = JSON.parse(cached); if (d && d.length >= 5) return d; } catch(_) {}
  }
  try {
    var data = await jsonp('https://api.fund.eastmoney.com/f10/lsjz?fundCode=' + code + '&pageIndex=1&pageSize=25', 8000);
    if (data && data.Data && data.Data.LSJZList && data.Data.LSJZList.length > 5) {
      var navs = data.Data.LSJZList.map(function(x) { return parseFloat(x.NAV); })
        .filter(function(x) { return x && !isNaN(x); }).reverse();
      if (navs.length >= 5) {
        localStorage.setItem(key, JSON.stringify(navs));
        return navs;
      }
    }
  } catch(_) {}
  if (typeof PRECOMPUTED_NAV !== 'undefined' && PRECOMPUTED_NAV[code]) {
    var d = PRECOMPUTED_NAV[code];
    return [d.navPrev || d.nav, d.nav].filter(function(x) { return x && !isNaN(x); });
  }
  return null;
}

var trendCache = {};

async function loadAllTrends(funds) {
  var promises = funds.map(function(f) {
    return fetchFundHistory(f.code).then(function(navs) {
      if (navs && navs.length > 1) {
        trendCache[f.code] = navs;
        var row = document.querySelector('.fund-row[data-code="' + f.code + '"]');
        if (row) {
          var td = row.querySelector('.trend-cell');
          if (td) {
            td.innerHTML = sparkline(navs, 55, 20, parseFloat(f.change || 0) >= 0);
          }
        }
      }
    }).catch(function() {});
  });
  await Promise.allSettled(promises);
}

function injectSparklines() {
  var rows = document.querySelectorAll('.fund-row');
  rows.forEach(function(row) {
    if (!row.querySelector('.trend-cell')) {
      var signalCell = row.querySelector('.signal');
      if (signalCell) {
        var td = document.createElement('div');
        td.className = 'trend-cell hide-m';
        td.innerHTML = '<span style="font-size:10px;color:var(--text-dim)">...</span>';
        signalCell.parentNode.insertBefore(td, signalCell);
      }
    }
  });
}