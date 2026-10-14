import { test } from 'node:test';
import assert from 'node:assert/strict';
import { CvWorkflow } from '../src/app/cv-workflow.ts';

const file = (name='actual.pdf', bytes='%PDF-valid', type='application/pdf') => new File([bytes], name, {type});
const ready = (id='a'.repeat(32), name='actual.pdf') => ({document_id:id,filename:name,size_bytes:100,status:'ready',processable:true,characters:45});
const profile = (doc='a'.repeat(32), name='Sofía Vega') => ({document_id:doc,candidate_id:'c'.repeat(32),profile:{name}});
const reply = (data,status=200) => new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json'}});
const deferred = () => { let resolve; const promise=new Promise(r=>{resolve=r;});return {promise,resolve}; };
const settled = () => new Promise(resolve=>setImmediate(resolve));

async function prepare(request) { const w=new CvWorkflow('http://test',request);w.select(file());await w.upload();return w; }

test('ID sin validación no habilita extracción',async()=>{
 let calls=0;const w=await prepare(async()=>{calls++;return reply({document_id:'a'.repeat(32)});});
 assert.equal(w.getSnapshot().phase,'rejected');assert.equal(w.getSnapshot().document,null);
 w.setConsent(true);await w.generate();assert.equal(calls,1);
});

test('PDF válido exige consentimiento y genera solo desde documento validado',async()=>{
 const calls=[];const w=await prepare(async(url,options)=>{calls.push({url,options});return reply(calls.length===1?ready():profile());});
 assert.equal(w.getSnapshot().phase,'ready');await w.generate();assert.equal(calls.length,1);
 w.setConsent(true);await w.generate();assert.equal(calls.length,2);
 assert.deepEqual(JSON.parse(calls[1].options.body),{consent_external_processing:true});
 assert.equal(w.getSnapshot().profile.profile.name,'Sofía Vega');
});

for (const [name,body,type,message] of [['foto.png','PNG','image/png','Formato'],['cv.txt','txt','text/plain','Formato'],['vacio.pdf','','application/pdf','vacío']]) {
 test(`rechazo local de ${name}`,async()=>{
  let calls=0;const w=new CvWorkflow('',async()=>{calls++;return reply(ready());});
  w.select(file(name,body,type));await w.upload();w.setConsent(true);await w.generate();
  assert.equal(calls,0);assert.equal(w.getSnapshot().document,null);assert.match(w.getSnapshot().message,new RegExp(message));
 });
}

for (const [status,detail] of [[422,'No se encontró texto útil'],[422,'PDF dañado'],[422,'Cabecera inválida'],[413,'Supera el límite']]) {
 test(`rechazo del servidor: ${detail}`,async()=>{
  let calls=0;const w=await prepare(async()=>{calls++;return reply({detail},status);});
  assert.equal(w.getSnapshot().document,null);assert.equal(w.getSnapshot().phase,'rejected');
  w.setConsent(true);await w.generate();assert.equal(calls,1);assert.equal(w.getSnapshot().message,detail);
 });
}

test('perfil anterior seguido de carga inválida no reutiliza documento ni resultado',async()=>{
 let calls=0;const w=await prepare(async()=>reply(++calls===1?ready():calls===2?profile():{detail:'PDF dañado'},calls===3?422:200));
 w.setConsent(true);await w.generate();const saved=w.getSnapshot().profile;
 w.select(file('otro.pdf'));assert.equal(w.getSnapshot().document,null);assert.equal(w.getSnapshot().profile,null);assert.equal(w.getSnapshot().consent,false);
 await w.upload();await w.generate();assert.equal(calls,3);assert.equal(saved.profile.name,'Sofía Vega');
 assert.equal(w.getSnapshot().profile,null);
});

test('cambiar archivo durante carga descarta éxito tardío aun si fetch ignora abort',async()=>{
 const old=deferred();let calls=0;let firstSignal;
 const w=new CvWorkflow('',async(url,options)=>{calls++;if(calls===1){firstSignal=options.signal;return old.promise;}return reply(ready('b'.repeat(32),'nuevo.pdf'));});
 w.select(file('anterior.pdf'));const pending=w.upload();
 w.select(file('nuevo.pdf'));assert.equal(firstSignal.aborted,true);
 await w.upload();old.resolve(reply(ready()));await pending;
 assert.equal(w.getSnapshot().document.document_id,'b'.repeat(32));assert.equal(w.getSnapshot().file.name,'nuevo.pdf');assert.equal(w.getSnapshot().phase,'ready');
});

test('cambiar archivo durante lectura JSON descarta validación tardía',async()=>{
 const json=deferred();const w=new CvWorkflow('',async()=>({ok:true,json:()=>json.promise}));
 w.select(file('anterior.pdf'));const pending=w.upload();await settled();assert.equal(w.getSnapshot().phase,'validating');
 w.select(file('nuevo.pdf'));json.resolve(ready());await pending;
 assert.equal(w.getSnapshot().phase,'selected');assert.equal(w.getSnapshot().document,null);
});

for(const fail of [false,true]) test(`extracción anterior tardía (${fail?'error':'éxito'}) no reemplaza nueva operación`,async()=>{
 const old=deferred();let calls=0;
 const w=await prepare(async()=>{calls++;if(calls===2)return old.promise;return reply(ready(calls===1?'a'.repeat(32):'b'.repeat(32)));});
 w.setConsent(true);const pending=w.generate();w.select(file('nuevo.pdf'));await w.upload();
 const current=w.getSnapshot();old.resolve(reply(fail?{detail:'Error viejo'}:profile(),fail?502:200));await pending;
 assert.equal(w.getSnapshot(),current);assert.equal(w.getSnapshot().document.document_id,'b'.repeat(32));assert.equal(w.getSnapshot().profile,null);
});

test('fallo del proveedor conserva documento para reintentar sin crear perfil ficticio',async()=>{
 let calls=0;const w=await prepare(async()=>{calls++;return calls===1?reply(ready()):calls===2?reply({detail:'El proveedor falló. Puedes reintentar.'},502):reply(profile());});
 w.setConsent(true);await w.generate();assert.equal(w.getSnapshot().phase,'provider_error');assert.equal(w.getSnapshot().profile,null);assert.ok(w.getSnapshot().document);assert.match(w.getSnapshot().message,/proveedor/);
 await w.generate();assert.equal(w.getSnapshot().phase,'generated');
});

test('API invalida documento antes aceptado: revoca permiso de extracción',async()=>{
 let calls=0;const w=await prepare(async()=>++calls===1?reply(ready()):reply({detail:'PDF dañado'},422));
 w.setConsent(true);await w.generate();assert.equal(w.getSnapshot().document,null);assert.equal(w.getSnapshot().consent,false);
 await w.generate();assert.equal(calls,2);
});

test('respuesta de otro documento nunca se presenta como resultado actual',async()=>{
 let calls=0;const w=await prepare(async()=>reply(++calls===1?ready():profile('b'.repeat(32))));
 w.setConsent(true);await w.generate();assert.equal(w.getSnapshot().profile,null);assert.equal(w.getSnapshot().phase,'provider_error');
});


test('el transporte no recibe la instancia del flujo como receptor de Window',async()=>{
 const w=await prepare(async function(){assert.equal(this,undefined);return reply(ready());});
 assert.equal(w.getSnapshot().phase,'ready');
});

test('recarga del mismo archivo muestra perfil guardado sin llamar a generar',async()=>{
 let calls=0;const saved={...profile(),status:'reused',updated_at:'2026-10-13T10:00:00'};
 const w=await prepare(async()=>{calls++;return reply({...ready(),saved_profile:saved});});
 assert.equal(calls,1);assert.equal(w.getSnapshot().profile.candidate_id,saved.candidate_id);
 assert.equal(w.getSnapshot().consent,false);assert.match(w.getSnapshot().message,/perfil guardado/);
});

test('doble clic de generación envía una sola petición',async()=>{
 const pending=deferred();let calls=0;
 const w=await prepare(async()=>++calls===1?reply(ready()):pending.promise);
 w.setConsent(true);const first=w.generate();await w.generate();assert.equal(calls,2);
 pending.resolve(reply({...profile(),status:'reused'}));await first;
 assert.match(w.getSnapshot().message,/perfil guardado/);
});

test('regeneración exige acción explícita y envía la versión guardada',async()=>{
 const saved={...profile(),status:'reused',updated_at:'2026-10-13T10:00:00'};
 let calls=0;let body;
 const w=await prepare(async(url,options)=>{calls++;if(calls===1)return reply({...ready(),saved_profile:saved});body=JSON.parse(options.body);return reply({...saved,status:'regenerated'});});
 await w.generate(true);assert.equal(calls,1);
 w.setConsent(true);await w.generate(true);
 assert.equal(body.regenerate,true);assert.equal(body.expected_updated_at,saved.updated_at);
 assert.equal(w.getSnapshot().profile.candidate_id,saved.candidate_id);
});
