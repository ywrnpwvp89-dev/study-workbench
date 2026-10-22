'use strict';
const $=id=>document.getElementById(id),val=id=>$(id).value.trim();
function el(tag,text,cls){const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;}
function download(name,content,type='text/plain;charset=utf-8'){const url=URL.createObjectURL(content instanceof Blob?content:new Blob([content],{type}));const a=el('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);}
function guard(id,fn){try{fn();}catch(e){$(id).textContent=e.message;}}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>{document.querySelectorAll('.pane').forEach(p=>p.hidden=p.id!==b.dataset.tab);document.querySelectorAll('nav button').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));});
let pdfURL;
$('makePdf').onclick=async()=>{
 const b=$('makePdf');b.disabled=true;
 try{
  const file=$('pdf').files[0];if(!file)throw Error('请先选择PDF');
  if(!globalThis.PDFLib)throw Error('PDF库未加载，请检查vendor文件');
  $('pdfStatus').textContent='正在本地排版…';
  const src=await PDFLib.PDFDocument.load(await file.arrayBuffer()),dst=await PDFLib.PDFDocument.create();
  const pages=await dst.embedPages(src.getPages());const mm=72/25.4,W=297*mm,H=210*mm,margin=5*mm,gap=4*mm,slot=(W-margin*2-gap)/2;
  for(let i=0;i<pages.length;i+=2){const page=dst.addPage([W,H]);for(let j=0;j<2;j++)if(pages[i+j]){const p=pages[i+j],scale=Math.min(slot/p.width,(H-2*margin)/p.height),w=p.width*scale,h=p.height*scale;page.drawPage(p,{x:margin+j*(slot+gap)+(slot-w)/2,y:(H-h)/2,width:w,height:h});}}
  if(dst.getPageCount()%2)dst.addPage([W,H]);
  const blob=new Blob([await dst.save()],{type:'application/pdf'});
  download('handout-a4-duplex.pdf',blob);if(pdfURL)URL.revokeObjectURL(pdfURL);pdfURL=URL.createObjectURL(blob);$('pdfPreview').src=pdfURL;$('pdfPreview').hidden=false;
  $('pdfStatus').textContent=`原稿${pages.length}页 → ${dst.getPageCount()}个打印面 → ${dst.getPageCount()/2}张双面A4。已下载；预览可核对页序。扫描页保留原图。表单/批注或特殊PDF请核对导出预览。`;
 }catch(e){$('pdfStatus').textContent='未生成：'+e.message;}finally{b.disabled=false;}
};
let tasks=[],coverage=null;
const statuses=['pending','in_progress','done','cancelled','needs_confirmation'];
function renderTasks(){
 $('coverage').textContent=coverage?'采集覆盖：'+JSON.stringify(coverage):'覆盖范围未提供；不能推断所有来源已经读完。';
 const host=$('taskList');host.replaceChildren();
 tasks.forEach(t=>{if(val('taskFilter')!=='all'&&t.status!==val('taskFilter'))return;const c=el('article',null,'card');c.append(el('h3',t.title),el('small','负责人：'+(t.owner||'待确认')+' · 截止：'+(t.due||'待确认')),el('p','证据：'+(t.evidence_ids||[]).join(' / ')),el('p',t.rationale||''));const s=el('select');s.setAttribute('aria-label',t.title+'状态');statuses.forEach(k=>{const o=el('option',k);o.value=k;s.append(o);});s.value=t.status;s.onchange=()=>{t.status=s.value;renderTasks();};c.append(s);host.append(c);});
}
$('tasksFile').onchange=async e=>{try{const d=JSON.parse(await e.target.files[0].text()),items=Array.isArray(d)?d:d.items;if(!Array.isArray(items)||items.some(t=>!t||typeof t.title!=='string'||!statuses.includes(t.status)||!Array.isArray(t.evidence_ids)||t.evidence_ids.some(id=>typeof id!=='string')))throw Error('需要包含title、有效status、evidence_ids数组的任务');tasks=items;coverage=Array.isArray(d)?null:d.coverage;$('tasksStatus').textContent='已导入 '+tasks.length+' 条；证据ID仅显示，网页未连接原始证据库。';renderTasks();}catch(e){$('tasksStatus').textContent=e.message;}};
$('tasksSample').onclick=()=>{tasks=[{title:'虚构示例：核对实验报告',owner:null,due:null,status:'needs_confirmation',evidence_ids:['demo:001'],rationale:'这是演示数据，不代表任何人的真实任务。'}];coverage={status:'demo',sources:[]};renderTasks();};
$('tasksExport').onclick=()=>download('work-items.json',JSON.stringify({items:tasks,coverage},null,2),'application/json');$('taskFilter').onchange=renderTasks;renderTasks();
let questions=[];
function renderQuestions(){const host=$('questionList');host.replaceChildren();questions.forEach((q,i)=>{const c=el('article',null,'card');c.append(el('h3',(i+1)+'. '+q.question),el('p','依据：'+q.basis),el('p','追问：'+q.followup));const b=el('button','删除');b.onclick=()=>{questions.splice(i,1);renderQuestions();};c.append(b);host.append(c);});}
$('addQuestion').onclick=()=>guard('interviewStatus',()=>{if(!val('question'))throw Error('请填写主问题');questions.push({question:val('question'),basis:val('basis')||'待确认来源',followup:val('followup')||'无'});['question','basis','followup'].forEach(k=>$(k).value='');renderQuestions();$('interviewStatus').textContent=`共${questions.length}题；建议另外留出开场/同意/结束时间。`;});
$('interviewExport').onclick=()=>download('interview-guide.md',`# ${val('topic')||'研究访谈提纲'}\n\n角色：${val('role')||'待确认'}\n总时长：${val('interviewMinutes')}分钟（含开场与结束）\n\n`+questions.map((q,i)=>`## ${i+1}. ${q.question}\n依据：${q.basis}\n追问：${q.followup}\n现场记录：\n`).join('\n'));
let notes=[];
function checkNotes(ns){if(!Array.isArray(ns)||ns.some(n=>!n||typeof n.id!=='string'||!n.id.trim()||typeof n.title!=='string'||!['EXTRACTED','INFERRED','UNVERIFIED'].includes(n.type)))throw Error('来源卡需要id、title和有效type');if(new Set(ns.map(n=>n.id)).size!==ns.length)throw Error('来源ID重复，请先核对版本');}
function renderNotes(){const host=$('noteList');host.replaceChildren();notes.forEach((n,i)=>{const c=el('article',null,'card');c.append(el('h3',n.title),el('small',n.id+' · '+n.type),el('p',n.claim),el('p',[n.publisher,n.published,n.locator].filter(Boolean).join(' / ')));const b=el('button','删除');b.onclick=()=>{notes.splice(i,1);renderNotes();};c.append(b);host.append(c);});}
$('addNote').onclick=()=>guard('notesStatus',()=>{const n={id:val('sourceId'),title:val('noteTitle'),type:val('claimType'),publisher:val('publisher'),published:val('published'),locator:val('locator'),claim:val('claim')};checkNotes([...notes,n]);if(!n.title||!n.claim)throw Error('请填写标题和内容');notes.push(n);renderNotes();$('notesStatus').textContent='来源卡已加入，离开前请导出。';});
$('notesExport').onclick=()=>download('source-cards.md',notes.map(n=>`# ${n.title}\n\n来源ID：${n.id}\n类型：${n.type}\n发布者：${n.publisher||'待确认'}\n日期：${n.published||'待确认'}\n定位：${n.locator||'待确认'}\n\n${n.claim}\n`).join('\n---\n'));
$('notesJson').onclick=()=>download('source-cards.json',JSON.stringify(notes,null,2),'application/json');
$('notesImport').onchange=async e=>{try{const d=JSON.parse(await e.target.files[0].text());checkNotes(d);notes=d;renderNotes();$('notesStatus').textContent='已导入 '+notes.length+' 张来源卡';}catch(e){$('notesStatus').textContent=e.message;}};
let courses=[];
const days=['一','二','三','四','五','六','日'];
function courseBlock(c,idx){const n=el('div',null,'event '+(c.online?'online':'c'+idx%4));n.append(el('strong',c.name),el('small',(c.code||'待确认代码')+'/'+(c.section||'待确认班号')),el('small',(c.teacher||'教师待确认')+' · '+(c.room||'地点待确认')),el('small',(c.online?'在线 · ':'')+'第'+(c.weeks||'待确认')+'周'));return n;}
function renderCourses(){
 const a=Workbench.audit(courses);$('creditAudit').textContent=`已知学分：${a.arithmetic} = ${a.total}；已知${a.known}/${a.groups}门，同一代码/班号只计一次学分。不自动判断毕业/学期达标；缺少代码或班号时不能自动去重。`;
 const rows=$('courseRows');rows.replaceChildren();courses.forEach((c,i)=>{const tr=el('tr');[c.day&&c.start&&c.end?`周${days[c.day-1]} 第${c.start}—${c.end}节`:'待确认时间',`${c.code||'待确认代码'}/${c.section||'待确认班号'}`,c.name+' / '+(c.nature||'性质待确认'),c.credit??'待确认',(c.teacher||'待确认')+' / '+(c.room||'待确认'),(c.weeks||'待确认')+' / '+(c.exam||'考试待确认'),(c.online?'在线；':'')+(c.eligibility||'对象待确认')+'；'+(c.remark||'')].forEach(v=>tr.append(el('td',v)));const td=el('td'),b=el('button','删除');b.onclick=()=>{courses.splice(i,1);renderCourses();};td.append(b);tr.append(td);rows.append(tr);});
 const cf=$('conflicts');cf.replaceChildren();if(!a.conflicts.length)cf.append(el('p','已知上课时间未检测到重叠；待确认时间与考试尚不能判断无冲突。'));a.conflicts.forEach(x=>cf.append(el('p',`${courses[x.a].name} / ${courses[x.b].name}：第${x.weeks.join(',')}周重叠。若已解决，请以当前选课系统为准。`,'conflict')));
 const u=$('unknowns');u.replaceChildren();a.unknown.forEach(t=>u.append(el('p',t)));if(!a.unknown.length)u.append(el('p','字段无缺失；仍需核对官方来源及考试是否冲突。'));
 $('calendarTitle').textContent=(val('term')||'课程安排')+' · 第'+val('week')+'周';
 const cal=$('calendar');cal.replaceChildren();cal.append(el('div','节次','cell heading'));days.forEach(d=>cal.append(el('div','周'+d,'cell heading')));
 const week=Number(val('week')),es=Workbench.events(courses),max=Math.max(12,...courses.map(c=>c.end||0));
 for(let p=1;p<=max;p++){cal.append(el('div','第'+p+'节','cell'));for(let d=1;d<=7;d++){const cell=el('div',null,'cell');es.forEach((c,i)=>{if(c.day===d&&c.start&&c.end&&c.weekSet?.includes(week)&&c.start<=p&&c.end>=p){if(c.start===p)cell.append(courseBlock(c,i));else cell.append(el('div',c.name+'（续）','event '+(c.online?'online':'c'+i%4)));}});cal.append(cell);}}
 const fl=$('floating');fl.replaceChildren();es.forEach((c,i)=>{if(!c.day||!c.start||!c.end||!c.weekSet)fl.append(courseBlock(c,i));});
}
$('addCourse').onclick=()=>guard('courseStatus',()=>{const c={name:val('courseName'),code:val('courseCode'),section:val('section'),credit:val('credit')?Number(val('credit')):null,teacher:val('teacher'),room:val('room'),nature:val('nature'),eligibility:val('eligibility'),day:val('day')?Number(val('day')):null,start:val('start')?Number(val('start')):null,end:val('end')?Number(val('end')):null,weeks:val('weeks'),exam:val('exam'),remark:val('remark'),online:$('online').checked};Workbench.validateCourse(c);Workbench.audit([...courses,c]);courses.push(c);renderCourses();$('courseStatus').textContent='已添加；字段未核实不代表课程可选。';});
$('coursesImport').onchange=async e=>{try{const d=JSON.parse(await e.target.files[0].text());if(!Array.isArray(d))throw Error('课程JSON必须是数组');const cs=d.map(Workbench.validateCourse);Workbench.audit(cs);courses=cs;renderCourses();$('courseStatus').textContent='已导入 '+courses.length+' 门';}catch(e){$('courseStatus').textContent=e.message;}};
$('coursesExport').onclick=()=>download('timetable.json',JSON.stringify(courses,null,2),'application/json');$('coursesMd').onclick=()=>download('timetable.md',Workbench.markdown(courses,val('term')));$('week').oninput=()=>{if(Number(val('week'))>=1&&Number(val('week'))<=60)renderCourses();};$('term').oninput=renderCourses;$('printView').onclick=()=>window.print();renderCourses();
