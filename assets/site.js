(()=>{'use strict';
const $=s=>document.querySelector(s);
document.addEventListener('DOMContentLoaded',()=>{
  const date=$('#todayDate'), year=$('#year');
  if(date) date.textContent=new Intl.DateTimeFormat('ar-IQ',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).format(new Date())+' — كركوك، العراق';
  if(year) year.textContent=String(new Date().getFullYear());

  const form=$('#siteSearch'), input=$('#searchInput');
  let status=$('#searchStatus');
  if(form&&!status){status=document.createElement('p');status.id='searchStatus';status.className='search-status';status.setAttribute('role','status');status.setAttribute('aria-live','polite');form.insertAdjacentElement('afterend',status)}
  form?.addEventListener('submit',e=>{
    e.preventDefault();
    const q=(input?.value||'').trim().toLocaleLowerCase('ar');
    if(!q){if(status)status.textContent='اكتب كلمة للبحث.';return}
    const text=document.body.innerText.toLocaleLowerCase('ar');
    if(status)status.textContent=text.includes(q)?'عُثر على الكلمة في محتوى الصفحة.':'لا توجد نتائج مطابقة حالياً. أضف أخباراً منشورة لتظهر نتائج البحث.';
  });
  input?.addEventListener('input',()=>{if(!input.value.trim()&&status)status.textContent=''});

  const newsletter=$('#newsletterForm');
  newsletter?.addEventListener('submit',e=>{
    e.preventDefault();
    const output=$('#newsletterStatus');
    if(output) output.textContent='شكراً لاهتمامك؛ خدمة الاشتراك ستُفعّل قريباً.';
  });

  document.querySelectorAll('.nav a[data-filter]').forEach(link=>{
    link.addEventListener('click',()=>{
      document.querySelectorAll('.nav a').forEach(a=>a.classList.toggle('active',a===link));
      const filter=link.dataset.filter;
      if(filter!=='all'){
        const section=$('#iraq');
        const title=$('#latestTitle');
        if(title) title.textContent='أبرز الأخبار — '+filter;
        if(section) section.scrollIntoView({behavior:'smooth',block:'start'});
      }else if($('#latestTitle')) $('#latestTitle').textContent='أبرز الأخبار';
    });
  });

  document.querySelectorAll('img').forEach(img=>{
    img.addEventListener('error',()=>{
      if(img.dataset.fallback)return;
      img.dataset.fallback='1';
      img.src='assets/news-placeholder.svg';
    });
  });
});
})();