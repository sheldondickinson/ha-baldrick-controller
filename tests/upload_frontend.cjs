const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('pixeltool/static/app.js','utf8');
const handler=source.slice(source.indexOf("function uploadFeedback("),source.indexOf("$('model').onchange="));
async function check(existing,invalid=false){
 const calls=[],elements={}; const raw=Buffer.from('<custommodel name="XML test" CustomModel="1,2,3"/>');
 const file={name:'test.xml',size:raw.length,arrayBuffer:async()=>raw};
 const model={id:'uploaded',title:'XML test',count:3};
 const feedback=[];class Reader{readAsArrayBuffer(f){this.onprogress({lengthComputable:true,loaded:raw.length/2,total:raw.length});this.result=raw;this.onload();}}
 const context={FileReader:Reader,Uint8Array,btoa:s=>Buffer.from(s,'binary').toString('base64'),session:existing?'owner':null,status:{state:{}},instance:{id:'old'},previewColours:[],model:null,library:{models:[model]},$:id=>elements[id]??=(id==='upload'?{files:[file]}:id==='uploadProgress'?{removeAttribute:()=>feedback.push('indeterminate')}:{}),action:fn=>fn(),api:async op=>{calls.push(op);if(op==='upload'){if(invalid)throw Error('Unsafe or malformed model XML');return model;}return {session:'temporary',state:{},armed:false};},refresh:async()=>{},showModel:()=>{},draw:()=>{},renderStatus:()=>{}};
 vm.createContext(context);vm.runInContext(handler,context);
 if(invalid)await assert.rejects(context.$('upload').onchange(),/malformed/);else{await context.$('upload').onchange();assert.equal(context.instance,null);assert.equal(context.model.id,'uploaded');assert(context.$('uploadStatus').textContent.includes('Saved XML test'));assert.equal(context.$('uploadProgress').value,100);}
 assert(!calls.includes('arm'));assert.equal(context.$('upload').disabled,false);assert.equal(context.$('upload').value,'');assert(feedback.includes('indeterminate'));if(invalid)assert(context.$('uploadStatus').textContent.includes('Upload failed')); 
 if(existing){assert.equal(context.session,'owner');assert(!calls.includes('claim'));assert(!calls.includes('release'));}else{assert.equal(context.session,null);assert.equal(calls[0],'claim');assert.equal(calls.at(-1),'release');}
}
(async()=>{await check(false);await check(true);await check(false,true);console.log('XML upload: selection, save, disarmed lease and failure cleanup passed');})().catch(e=>{console.error(e);process.exit(1);});
