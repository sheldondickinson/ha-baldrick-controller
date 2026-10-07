const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('pixeltool/static/app.js','utf8');
const functions=['setState','touch','ensureSession','stopRelease','idleTick'];
function extract(name){const start=source.indexOf(`function ${name}(`),a=source.indexOf('{',source.indexOf('){',start)),end=source.indexOf('\n',a);return (source.slice(start-6,start)==='async '?'async ':'')+source.slice(start,end);}
(async()=>{
 let now=1000;const calls=[],elements={tool:{value:'pusher'},mode:{value:'4'},node:{value:'1'},level:{value:'12'},cap:{value:'5'},error:{}};
 const ctx={performance:{now:()=>now},session:null,status:{state:{},idle_timeout:60},lastActivity:now,lastPoll:0,instance:null,previewColours:null,$:id=>elements[id]??={},selectInstance:async()=>{calls.push(['select']);ctx.instance={};},renderStatus:()=>{},draw:()=>{},api:async(op,data={})=>{calls.push([op,data]);if(op==='claim')return {session:'owner',state:{},idle_timeout:60};if(op==='release')return {session_active:false,state:{},idle_timeout:60};return {state:data,armed:op==='arm',session_active:true,idle_timeout:60};}};
 vm.createContext(ctx);for(const fn of functions)vm.runInContext(extract(fn),ctx);
 await ctx.setState();assert.deepEqual(calls.map(x=>x[0]),['claim','select','state','arm']);assert.equal(ctx.session,'owner');
 calls.length=0;now+=25000;await ctx.idleTick();assert.equal(calls[0][0],'heartbeat');assert.equal(calls[0][1].idle_seconds,25);
 calls.length=0;now+=36000;await ctx.idleTick();assert.deepEqual(calls.map(x=>x[0]),['stop','release']);assert.equal(ctx.session,null);assert(elements.error.textContent.includes('inactivity'));
 calls.length=0;elements.tool.value='tools';elements.mode.value='0';await ctx.setState();assert(!calls.some(x=>x[0]==='arm'));assert(calls.some(x=>x[0]==='stop'));
 console.log('Automatic output and idle blackout/release passed');
})().catch(e=>{console.error(e);process.exit(1);});
