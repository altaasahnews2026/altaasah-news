(()=>{'use strict';
const $=s=>document.querySelector(s), $$=s=>Array.from(document.querySelectorAll(s));
document.addEventListener('DOMContentLoaded',()=>{
 const date=$('#todayDate'),year=$('#year');
 if(date)date.textContent=new Intl.DateTimeFormat('ar-IQ',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date())+' — كركوك، العراق';
 if(year)year.textContent=String(new Date().getFullYear());

 const form=$('#siteSearch'),input=$('#searchInput');
 const navLinks=$$('.nav a[data-filter]');
 let activeCategory='all',searchTerm='';
 const searchable=$$('.news-card,.most li,.media-cards article');
 let status=$('#searchStatus');
 const statusNode=()=>{
  if(!status&&form){status=document.createElement('p');status.id='searchStatus';status.className='search-status';status.setAttribute('role','status');form.insertAdjacentElement('afterend',status)}
  return status;
 };
 const categoryOf=item=>(item.querySelector('.category')?.textContent||'').trim();
 const matchesCategory=item=>{
  if(activeCategory==='all')return true;
  const category=categoryOf(item);
  if(activeCategory==='العراق')return ['كركوك','العراق','اقتصاد','رياضة'].includes(category)||item.textContent.includes('العراق');
  return category===activeCategory||item.textContent.includes(activeCategory);
 };
 const applyFilters=()=>{
  let count=0;
  searchable.forEach(item=>{
   const matchesText=!searchTerm||item.textContent.toLocaleLowerCase('ar').includes(searchTerm);
   const matchesGroup=!item.classList.contains('news-card')||matchesCategory(item);
   const show=matchesText&&matchesGroup;
   item.hidden=!show;
   if(show)count++;
  });
  const note=statusNode();
  if(note){
   if(searchTerm)note.textContent='نتائج البحث عن «'+searchTerm+'»: '+count;
   else if(activeCategory!=='all')note.textContent='مواد قسم '+activeCategory+': '+count;
   else note.textContent='';
  }
  const title=$('#latestTitle');
  if(title)title.textContent=activeCategory==='all'?'أبرز الأخبار':'أبرز الأخبار — '+activeCategory;
 };
 form?.addEventListener('submit',e=>{
  e.preventDefault();
  searchTerm=(input?.value||'').trim().toLocaleLowerCase('ar');
  applyFilters();
  statusNode()?.scrollIntoView({behavior:'smooth',block:'nearest'});
 });
 input?.addEventListener('input',()=>{
  searchTerm=(input.value||'').trim().toLocaleLowerCase('ar');
  if(!searchTerm)applyFilters();
 });
 input?.addEventListener('keydown',e=>{
  if(e.key==='Escape'){input.value='';searchTerm='';applyFilters();input.blur()}
 });
 navLinks.forEach(link=>link.addEventListener('click',()=>{
  activeCategory=link.dataset.filter||'all';
  navLinks.forEach(a=>{
   const active=a===link;
   a.classList.toggle('active',active);
   if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
  });
  searchTerm='';
  if(input)input.value='';
  applyFilters();
  if(activeCategory!=='all')$('#iraq')?.scrollIntoView({behavior:'smooth',block:'start'});
 }));
 $$('img').forEach(img=>{
  img.addEventListener('error',()=>{
   if(img.dataset.fallback)return;
   img.dataset.fallback='1';img.src='assets/news-placeholder.svg';
  });
 });
 const track=$('#tickerTrack');
 if(track&&!track.dataset.cloned){track.innerHTML+=track.innerHTML;track.dataset.cloned='1'}
 const top=document.createElement('button');
 top.type='button';top.className='back-top';top.textContent='↑';top.setAttribute('aria-label','العودة إلى أعلى الصفحة');
 document.body.appendChild(top);
 const toggleTop=()=>top.classList.toggle('visible',window.scrollY>420);
 window.addEventListener('scroll',toggleTop,{passive:true});
 top.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
 toggleTop();
});
})();