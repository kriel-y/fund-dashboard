// Cloudflare Worker — 基金数据代理
// 解决公司网络拦截东方财富API的问题
// 部署后获得一个 workers.dev 域名，配到 Dashboard 里即可实时获取所有数据

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // ===== 1. 基金实时估值 /fund/022122 =====
    let m = path.match(/^\/fund\/(\d{6})$/);
    if (m) {
      const code = m[1];
      try {
        const resp = await fetch(`http://fundgz.1234567.com.cn/js/${code}.js`);
        const text = await resp.text();
        return new Response(text, {
          headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' },
        });
      } catch (e) {
        return new Response(
          `jsonpgz({"fundcode":"${code}","gsz":"--","gszzl":"--","dwjz":"","jzrq":"","name":"","gztime":""})`,
          { headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' } }
        );
      }
    }

    // ===== 2. 基金历史净值 /history/022122 =====
    m = path.match(/^\/history\/(\d{6})$/);
    if (m) {
      const code = m[1];
      try {
        const resp = await fetch(
          `https://api.fund.eastmoney.com/f10/lsjz?callback=jQuery&fundCode=${code}&pageIndex=1&pageSize=25`,
          { headers: { 'Referer': 'https://fund.eastmoney.com/' } }
        );
        const text = await resp.text();
        return new Response(text, {
          headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=gbk' },
        });
      } catch (e) {
        return new Response(`jQuery({})`, {
          headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' },
        });
      }
    }

    // ===== 3. 大盘指数 /index =====
    if (path === '/index') {
      try {
        const resp = await fetch(
          'https://hq.sinajs.cn/list=s_sh000001,s_sz399001,s_sz399006,s_sh000688,s_sh000300,s_sh000016,s_sz399852',
          { headers: { 'Referer': 'https://finance.sina.com.cn/' } }
        );
        const text = await resp.text();
        return new Response(text, {
          headers: { ...corsHeaders, 'Content-Type': 'text/plain; charset=gbk' },
        });
      } catch (e) {
        return new Response('', { headers: corsHeaders });
      }
    }

    return new Response('Fund Proxy Worker', { headers: corsHeaders });
  },
};