class BaldrickStrategy {
 static async generate(config,hass){
  const entries=await hass.callWS({type:'config_entries/get'});
  const ids=new Set(entries.filter(e=>e.domain==='baldrick_controller').map(e=>e.entry_id));
  const registry=await hass.callWS({type:'config/entity_registry/list'});
  const devices=await hass.callWS({type:'config/device_registry/list'});
  const boards=devices.filter(d=>d.config_entries.some(e=>ids.has(e)));
  const cards=[{type:'markdown',content:'# Baldrick Controller\nEast St Lights — live board monitoring. PixelTool owns its test sessions; external senders require coordination.'},{type:'button',name:'Open PixelTool',icon:'mdi:led-strip-variant',tap_action:{action:'navigate',navigation_path:'/pixeltool'}}];
  const views=[{title:'All boards',path:'overview',cards}];
  for(const d of boards){
   const entities=registry.filter(e=>e.device_id===d.id&&!e.disabled_by).map(e=>e.entity_id);
   const title=d.name_by_user||d.name||d.model;
   cards.push({type:'entities',title,entities:entities.filter(e=>/online|warnings|frame_rate|native_test/.test(e))});
   const individual=[{type:'entities',title,entities},{type:'button',name:'Open board web interface',tap_action:{action:'url',url_path:d.configuration_url}},{type:'button',name:'Open PixelTool',tap_action:{action:'navigate',navigation_path:'/pixeltool'}}];
   const charts=entities.filter(e=>/temperature|frame_rate/.test(e));if(charts.length)individual.push({type:'history-graph',title:'Health',hours_to_show:12,entities:charts});
   views.push({title,path:d.id,cards:individual});
  }
  return {title:'Baldrick Controller',views};
 }
}
customElements.define('ll-strategy-dashboard-baldrick-controller',class extends HTMLElement{static generate=BaldrickStrategy.generate;});
