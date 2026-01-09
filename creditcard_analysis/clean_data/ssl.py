import ssl
import certifi 
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager, ProxyManager

def build_ssl_context(cafile: str, relax_strict = True) -> ssl.SSLContext:
    ca = cafile or certifi.where()
    ctx = ssl.create_default_context(cafile = ca)
    
    if relax_strict and hasattr(ctx, 'verify_flags') and hasattr(ssl, 'VERIFY_X509_STRICT'):
        ctx.verify_flags &= ~ ssl.VERIFY_X509_STRICT 

    return ctx 

class SSLContextAdapter(HTTPAdapter):
    def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
        self._ssl_context = ssl_context
        super().__init__(**kwargs)
    
    def init_poolmanager(self, connections, maxsize, block = True, **pool_kwargs):
        self.poolmanager = PoolManager(
            num_pools   = connections,
            maxsize     = maxsize,
            block       = block,
            ssl_context = self._ssl_context,
            **pool_kwargs
        )

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        if proxy not in self.proxy_manager:
            self.proxy_manager[proxy] = ProxyManager(
                proxy_url = proxy,
                ssl_context = self._ssl_context,
                **proxy_kwargs
            )

        return self.proxy_manager[proxy]