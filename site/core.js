(function(root){
 'use strict';
 function weeks(raw){
  const s=String(raw||'').replace(/周/g,'').replace(/\s/g,'');
  if(!s)return null;
  const odd=s.endsWith('单'),even=s.endsWith('双'),clean=s.replace(/[单双]$/,'');
  const result=new Set();
  for(const part of clean.split(/[,，、]/)){
   if(!/^\d+(?:[-—–]\d+)?$/.test(part))throw Error('周次格式请用1-16、1-16单或2,4,6');
   const nums=part.split(/[-—–]/).map(Number),a=nums[0],b=nums[1]??a;
   if(a<1||b>60||a>b)throw Error('周次范围须在1—60且起点不大于终点');
   for(let n=a;n<=b;n++)if((!odd||n%2===1)&&(!even||n%2===0))result.add(n);
  }
  if(!result.size)throw Error('周次条件没有任何有效教学周');
  return [...result].sort((a,b)=>a-b);
 }
 function validateCourse(c){
  if(!c||typeof c!=='object'||Array.isArray(c)||typeof c.name!=='string'||!c.name.trim())throw Error('每门课程必须有名称');
  if(c.credit!==null&&c.credit!==undefined&&(typeof c.credit!=='number'||!Number.isFinite(c.credit)||c.credit<0))throw Error('学分须为非负数或null');
  for(const k of ['day','start','end'])if(c[k]!==null&&c[k]!==undefined&&(!Number.isInteger(c[k])||c[k]<1||c[k]>(k==='day'?7:30)))throw Error('星期或节次超出范围');
  if(c.start&&c.end&&c.start>c.end)throw Error('起始节不能晚于结束节');
  weeks(c.weeks);
  return {...c,name:c.name.trim()};
 }
 function events(courses){return courses.map(c=>({...c,weekSet:weeks(c.weeks)}));}
 function audit(courses){
  courses.forEach(validateCourse);let conflicts=[],unknown=[];
  const es=events(courses);
  for(const c of es){
   for(const k of ['code','section','teacher','room','nature','eligibility','weeks','exam'])if(!c[k])unknown.push(c.name+'：'+({section:'待确认班号',weeks:'周次待确认',exam:'考试安排待确认'}[k]||k+'待确认'));
   if(c.credit==null)unknown.push(c.name+'：学分待确认');
   if(!c.day||!c.start||!c.end)unknown.push(c.name+'：无固定时间或上课时间待确认');
  }
  for(let i=0;i<es.length;i++)for(let j=i+1;j<es.length;j++){
   const a=es[i],b=es[j];
   if(a.day&&a.start&&a.end&&b.day&&b.start&&b.end&&a.weekSet&&b.weekSet&&a.day===b.day&&a.start<=b.end&&b.start<=a.end){
    const shared=a.weekSet.filter(w=>b.weekSet.includes(w));
    if(shared.length)conflicts.push({a:i,b:j,weeks:shared});
   }
  }
  const groups=new Map();
  courses.forEach((c,i)=>{const key=c.code&&c.section?c.code+'/'+c.section:'unverified-'+i;if(groups.has(key)&&groups.get(key)!==c.credit)throw Error('同一代码/班号的学分不一致，请核对');groups.set(key,c.credit);});
  const credits=[...groups.values()].filter(c=>c!=null);
  return {conflicts,unknown,total:credits.reduce((a,b)=>a+b,0),known:credits.length,groups:groups.size,arithmetic:credits.join(' + ')||'0'};
 }
 function markdown(courses,title){
  const a=audit(courses),esc=v=>String(v??'待确认').replace(/\|/g,'\\|').replace(/\r?\n/g,' ');
  let s='# '+esc(title||'课程安排')+'\n\n|星期|节次|代码/班号|名称|学分|教师|周次|地点|性质|考试|对象/备注|\n|---|---|---|---|---|---|---|---|---|---|---|\n';
  courses.forEach(c=>{s+='|'+[c.day?'周'+['一','二','三','四','五','六','日'][c.day-1]:'待确认',c.start&&c.end?`第${c.start}—${c.end}节`:'待确认',`${c.code||'待确认代码'}/${c.section||'待确认班号'}`,c.name,c.credit,c.teacher,c.weeks,c.room,c.nature,c.exam,(c.online?'在线；':'')+(c.eligibility||'对象待确认')+'；'+(c.remark||'')].map(esc).join('|')+'|\n';});
  s+=`\n已知学分：${a.arithmetic} = ${a.total}（${a.known}/${a.groups}门）；同一代码/班号只计一次。未核对培养方案最低/上限。\n\n`;
  s+=a.conflicts.map(x=>`冲突：${courses[x.a].name} / ${courses[x.b].name}，第${x.weeks.join(',')}周；若用户已解决，请以当前选课系统为准。`).join('\n')||'已知时间未检测到重叠；缺失时间与考试仍须核实。';
  return s+'\n\n待确认：\n'+a.unknown.map(x=>'- '+x).join('\n');
 }
 const api={weeks,validateCourse,events,audit,markdown};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Workbench=api;
})(typeof globalThis!=='undefined'?globalThis:this);
