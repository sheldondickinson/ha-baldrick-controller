class PixelToolPanel extends HTMLElement {
  set hass(hass) {this._hass=hass;}
  connectedCallback(){
    if(this._frame)return;
    this.style.cssText='display:block;height:100%;';
    const frame=document.createElement('iframe');frame.src='/baldrick_controller_static/pixeltool/index.html?v=0.1.1';frame.title='PixelTool';frame.style.cssText='width:100%;height:100%;border:0';this.append(frame);this._frame=frame;
    this._listener=async e=>{
      if(e.origin!==location.origin||e.source!==frame.contentWindow||e.data?.type!=='pixeltool-api')return;
      let result,error;
      try{result=await this._hass.callApi('POST','baldrick_controller/pixeltool',e.data.payload);if(result.error)error=result.error;}
      catch(x){error=x.body?.error||x.message||'PixelTool request failed';}
      frame.contentWindow.postMessage({type:'pixeltool-result',id:e.data.id,result,error},location.origin);
    };
    window.addEventListener('message',this._listener);
  }
  disconnectedCallback(){window.removeEventListener('message',this._listener);this._frame=null;}
}
customElements.define('baldrick-pixeltool-panel',PixelToolPanel);
