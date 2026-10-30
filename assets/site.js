(()=>{'use strict';
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
document.addEventListener('DOMContentLoaded',()=>{
 const date=$('#todayDate'),year=$('#year');
 if(date)date.textContent=new Intl.DateTimeFormat('ar-IQ',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date())+' — كركوك، العراق';
 if(year)year.textContent=String(new Date().getFullYear());

 const form=$('#siteSearch'),input=$('#searchInput');
 form?.addEventListener('submit',e=>{
  e.preventDefault();
  const q=(input?.value||'').trim().toLocaleLowerCase('ar');
  const items=$$('.news-card,.most li,.media-cards article');
  let count=0;
  items.forEach(item=>{const match=!q||item.textContent.toLocaleLowerCase('ar').includes(q);item.hidden=!match;if(match)count++});
  let note=$('#searchStatus');
  if(!note){note=document.createElement('p');note.id='searchStatus';note.className='search-status';note.setAttribute('role','status');form.insertAdjacentElement('afterend',note)}
  note.textContent=q?'نتائج البحث: '+count:'تم عرض جميع المواد';
 });
 input?.addEventListener('input',()=>{if(!input.value.trim()){$$('.news-card,.most li,.media-cards article').forEach(item=>item.hidden=false);const n=$('#searchStatus');if(n)n.textContent=''}});

 $$('.nav a[data-filter]').forEach(link=>link.addEventListener('click',()=>{
  const key=link.dataset.filter;
  $$('.nav a').forEach(a=>a.classList.toggle('active',a===link));
  const items=$$('.news-card');
  items.forEach(item=>item.hidden=key!=='all'&&!item.textContent.includes(key));
  const title=$('#latestTitle');
  if(title)title.textContent=key==='all'?'أبرز الأخبار':'أبرز الأخبار — '+key;
  if(key!=='all')$('#iraq')?.scrollIntoView({behavior:'smooth',block:'start'});
 }));
 $$('img').forEach(img=>img.addEventListener('error',()=>{
  if(img.dataset.fallback)return;
  img.dataset.fallback='1';img.src='assets/news-placeholder.svg';
 }));
 const track=$('#tickerTrack');
 if(track&&!track.dataset.cloned){track.innerHTML+=track.innerHTML;track.dataset.cloned='1'}
});
})();