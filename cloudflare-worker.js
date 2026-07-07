// Cloudflare Worker — 基金净值HTTPS代理
// 部署步骤：
// 1. 打开 https://workers.cloudflare.com/
// 2. 注册/登录（免费）
// 3. 点「创建 Worker」
// 4. 粘贴本代码 → 点「保存并部署」
// 5. 复制生成的 workers.dev 域名

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS 头
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': '*',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // /fund/022122 → 代理基金净值
    const match = path.match(/^\/fund\/(\d{6})$/);
    if (match) {
      const code = match[1];
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

    return new Response('Fund Proxy Worker 🚀', { headers: corsHeaders });
  },
};
