(() =>  {
  const widget = document.getElementById('planner-weather-widget');
  const modal = document.getElementById('planner-modal');
  if (!widget || !modal) return;
  const dialog = modal.querySelector('[role="dialog"]');
  const grid = document.querySelector('.week-grid');
  const csrf = document.querySelector('input[name=csrfmiddlewaretoken]')?.value || '';
  const cookie = document.cookie.split('; ').find(v => v.startsWith('restyle_csrftoken='))?.split('=').slice(1).join('=');
  const token = cookie ? decodeURIComponent(cookie) : csrf;
  const $ = id => document.getElementById(id);
  const cacheKey = 'restylePlannerWeather';
  let state = null, activeDate = null, previousFocus = null, refreshTimer = null;
  let toast = null, currentController = null;
  let modalWeather = null, modalLocation = null, modalWeatherController = null, modalWeatherLoading = false;
  let modalSearchController = null, modalSearchTimer = null, modalWeatherVersion = 0;
  let lastSearchLocations = [];
  let searchTransitionTimer = null, finishSearchTransition = null;
  const weatherOverrideKey = 'restylePlannerModalLocation';
  const forecastCacheKey = 'restylePlannerForecasts';
  const forecastMemory = new Map();
  
  let weatherOverride = readWeatherOverride();

  const fmtDate = iso => new Intl.DateTimeFormat('en-GB',  {
    weekday:'long',day:'numeric',month:'long',year:'numeric'
  }).format(new Date(`${iso}T12:00:00`));

  const weatherIconKind = (label, theme) => /thunder|storm/i.test(label) ? 'storm' : /rain|drizzle/i.test(label) ? 'rain' : /snow/i.test(label) ? 'snow' : /sun|clear/i.test(label) || theme === 'sunny' ? 'sun' : /cloud|fog/i.test(label) ? 'cloud' : 'generic';

  function icon(kind)  {
    const svg = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox','0 0 24 24');
    svg.setAttribute('aria-hidden','true');
    svg.setAttribute('fill','none');
    svg.setAttribute('stroke','currentColor');
    svg.setAttribute('stroke-width','1.8');
    svg.setAttribute('stroke-linecap','round');
    svg.setAttribute('stroke-linejoin','round');
    const shapes= {
      location:[['path', {d:'M20 10c0 5-8 12-8 12S4 15 4 10a8 8 0 1 1 16 0Z'}],['circle', {cx:12,cy:10,r:2.5}]],
      sun:[['circle', {cx:12,cy:12,r:4}],['path', {d:'M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l-1.42 1.42m14.14-14.14 1.42-1.42'}]],
      cloud:[['path', {d:'M7 18h10a4 4 0 0 0 .4-8A6 6 0 0 0 6 11a3.5 3.5 0 0 0 1 7Z'}]],
      rain:[['path', {d:'M7 15h10a4 4 0 0 0 .4-8A6 6 0 0 0 6 8a3.5 3.5 0 0 0 1 7Z'}],['path', {d:'m8 18-1 2m6-2-1 2m6-2-1 2'}]],
      storm:[['path', {d:'M7 14h10a4 4 0 0 0 .4-8A6 6 0 0 0 6 7a3.5 3.5 0 0 0 1 7Z'}],['path', {d:'m13 14-3 5h3l-1 3 4-6h-3l1-2'}]],
      snow:[['path', {d:'M12 2v20m8.66-15-17.32 10m0-10 17.32 10'}]],
      generic:[['circle', {cx:12,cy:12,r:8}],['path', {d:'M12 8v4l3 2'}]]
    };
    (shapes[kind]||shapes.generic).forEach(([tag,attrs])=> {
      const e=document.createElementNS('http://www.w3.org/2000/svg',tag);
      Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));
      svg.append(e)
    });
    return svg;
  }

  function notify(type, text, existing=toast)  {
    if (window.updateToast && existing) toast=window.updateToast(existing,type,text);
    else if(window.showToast) toast=window.showToast(type,text);
  }

  function renderWidgetLoading()  {
    widget.classList.remove('weather-widget--no-permission');
    widget.classList.add('is-loading');
    $('weather-widget-condition').textContent='Loading weather';
    $('weather-widget-message').textContent='';
    $('weather-enable').hidden=true;
    $('weather-enable').disabled=false;
    $('weather-enable').removeAttribute('aria-busy');
    $('weather-refresh').hidden=false;
    $('weather-refresh').classList.add('is-loading');
    $('weather-refresh').disabled=true;
  }

  function renderWidgetError(message='Weather unavailable')  {
    widget.classList.remove('is-loading');
    widget.className='weather-widget weather-widget--neutral';
    $('weather-widget-icon').replaceChildren(icon('generic'));
    $('weather-widget-condition').textContent='Weather unavailable';
    $('weather-widget-temperature').hidden=true;
    $('weather-widget-location').hidden=true;
    $('weather-widget-message').textContent=message;
    $('weather-enable').className='mm-tool weather-enable';
    $('weather-enable').hidden=false;
    $('weather-enable').disabled=false;
    $('weather-enable').removeAttribute('aria-busy');
    $('weather-enable').textContent='Try again';
    $('weather-refresh').hidden=false;
    $('weather-refresh').classList.remove('is-loading');
    $('weather-refresh').disabled=false;
    publish(null);
    try {
      sessionStorage.removeItem(cacheKey)
    } catch(_) {
    }
  }

  function publish(next)  {
    state=next;
    window.plannerWeather=next;
    try {
      sessionStorage.setItem(cacheKey,JSON.stringify(next))
    } catch(_) {
    }
    window.dispatchEvent(new CustomEvent('weather:updated', {
      detail:next
    }));
  }

  function renderWeather(data)  {
    widget.classList.remove('is-loading');
    widget.className=`weather-widget weather-widget--${data.theme||'neutral'}`;
    $('weather-widget-icon').replaceChildren(icon(weatherIconKind(data.condition,data.theme)));
    $('weather-widget-condition').textContent=data.condition;
    $('weather-widget-temperature').hidden=false;
    $('weather-widget-temperature').querySelector('span').textContent=data.temperature+'\u00B0';
    $('weather-widget-location').hidden=false;
    $('weather-widget-location').querySelector('span').textContent=data.location;
    $('weather-widget-message').textContent='';
    $('weather-enable').hidden=true;
    $('weather-enable').disabled=false;
    $('weather-enable').removeAttribute('aria-busy');
    $('weather-refresh').hidden=false;
    $('weather-refresh').classList.remove('is-loading');
    $('weather-refresh').disabled=false;
    $('weather-attribution').hidden=false;
    publish(data);
  }

  function readCached()  {
    try  {
      const value=JSON.parse(sessionStorage.getItem(cacheKey)||'null');
      return value && value.timestamp ? value : null;
    } catch(_) {
      return null;
    }
  }

  function readWeatherOverride()  {
    try  {
      return JSON.parse(sessionStorage.getItem(weatherOverrideKey)||'null');
    } catch(_)  {
      return null;
    }
  }

  function localDateString(value=new Date())  {
    return [value.getFullYear(),String(value.getMonth()+1).padStart(2,'0'),String(value.getDate()).padStart(2,'0')].join('-');
  }

  function updateTodayHighlight()  {
    if(!grid) return;
    const today=localDateString();
    grid.querySelectorAll('.outfit-slot[data-date]').forEach(slot=> {
      slot.closest('.day-col')?.classList.toggle('is-today',slot.dataset.date===today);
    });
  }
  updateTodayHighlight();
  const todayRefreshTimer=window.setInterval(updateTodayHighlight,60000);

  function shortDate(iso)  {
    return new Intl.DateTimeFormat('en-GB', {
      weekday:'long',day:'numeric',month:'long'
    }).format(new Date(iso+'T12:00:00'));
  }

  function dateOffset(iso)  {
    const parts=iso.split('-').map(Number);
    const today=localDateString().split('-').map(Number);
    return (Date.UTC(parts[0],parts[1]-1,parts[2])-Date.UTC(today[0],today[1]-1,today[2]))/86400000;
  }

  function currentCoordinates()  {
    if(weatherOverride && Number.isFinite(Number(weatherOverride.latitude)) && Number.isFinite(Number(weatherOverride.longitude))) return weatherOverride;
    if(state && Number.isFinite(Number(state.latitude)) && Number.isFinite(Number(state.longitude))) return state;
    try  {
      const coords=JSON.parse(sessionStorage.getItem('restylePlannerLocation')||'null');
      if(coords && Number.isFinite(Number(coords.latitude)) && Number.isFinite(Number(coords.longitude))) return coords;
    } catch(_)  {
    }
    return null;
  }

  function resolvedLocation(coords)  {
    if(weatherOverride && Number(coords.latitude)===Number(weatherOverride.latitude) && Number(coords.longitude)===Number(weatherOverride.longitude)) return weatherOverride.name;
    if(state && Number(state.latitude)===Number(coords.latitude) && Number(state.longitude)===Number(coords.longitude)) return state.location;
    const cached=readCached();
    if(cached && Number(cached.latitude)===Number(coords.latitude) && Number(cached.longitude)===Number(coords.longitude)) return cached.location;
    return 'Current location';
  }

  function setModalCardClass(theme,extra='')  {
    $('modal-weather-card').className='weather-widget weather-widget--compact weather-widget--'+(theme||'neutral')+(extra?' '+extra:'');
  }

  function setModalLocation(name)  {
    modalLocation=name||'Current location';
    const location=$('modal-weather-location');
    location.hidden=!modalLocation;
    location.querySelector('span').textContent=modalLocation;
  }

  function setModalDateLabel()  {
    $('modal-weather-date').textContent=activeDate?'Weather in '+shortDate(activeDate):'';
  }

  function setModalActions(hasLocation)  {
    $('modal-weather-change').hidden=false;
    $('modal-weather-allow').hidden=hasLocation;
    $('modal-weather-use-current').hidden=!(weatherOverride||hasLocation);
    $('modal-weather-retry').hidden=true;
    $('modal-weather-change').textContent=hasLocation?'Change Location':'Search Location';
  }

  function showModalNeedsLocation()  {
    modalWeather=null;
    modalLocation='';
    modalWeatherLoading=false;
    setModalCardClass('no-permission');
    $('modal-weather-condition').textContent='Allow location';
    $('modal-weather-icon').replaceChildren(icon('generic'));
    $('modal-weather-temperature').hidden=true;
    $('modal-weather-location').hidden=true;
    $('modal-weather-message').textContent='';
    setModalDateLabel();
    setModalActions(false);
    renderLists();
  }

  function showModalLoading(location)  {
    modalWeather=null;
    modalWeatherLoading=true;
    setModalLocation(location);
    setModalCardClass('neutral','weather-widget--loading');
    $('modal-weather-condition').textContent='Loading forecast';
    $('modal-weather-icon').replaceChildren(icon('generic'));
    $('modal-weather-temperature').hidden=false;
    $('modal-weather-temperature').querySelector('span').textContent='Loading...';
    $('modal-weather-message').textContent='';
    setModalDateLabel();
    setModalActions(true);
    renderLists();
  }

  function showModalNoData(location)  {
    modalWeather= {
      no_data:true
    };
    modalWeatherLoading=false;
    setModalLocation(location);
    setModalCardClass('neutral');
    $('modal-weather-condition').textContent='No Data';
    $('modal-weather-icon').replaceChildren(icon('generic'));
    $('modal-weather-temperature').hidden=false;
    $('modal-weather-temperature').querySelector('span').textContent='No Data';
    $('modal-weather-message').textContent='';
    setModalDateLabel();
    setModalActions(true);
    renderLists();
  }

  function showModalError(location,message='Weather forecast is unavailable.')  {
    modalWeather=null;
    modalWeatherLoading=false;
    setModalLocation(location);
    setModalCardClass('neutral');
    $('modal-weather-condition').textContent='Weather unavailable';
    $('modal-weather-icon').replaceChildren(icon('generic'));
    $('modal-weather-temperature').hidden=true;
    $('modal-weather-message').textContent=message;
    setModalDateLabel();
    setModalActions(true);
    $('modal-weather-retry').hidden=false;
    renderLists();
  }

  function showModalWeather(data,location)  {
    modalWeather=data;
    modalWeatherLoading=false;
    setModalLocation(location);
    setModalCardClass(data.theme||'neutral');
    $('modal-weather-condition').textContent=data.condition;
    $('modal-weather-icon').replaceChildren(icon(weatherIconKind(data.condition,data.theme)));
    $('modal-weather-temperature').hidden=false;
    $('modal-weather-temperature').querySelector('span').textContent=data.temperature+'\u00B0';
    $('modal-weather-message').textContent='';
    setModalDateLabel();
    setModalActions(true);
    renderLists();
  }

  function getForecastCache(key)  {
    const memory=forecastMemory.get(key);
    if(memory && Date.now()-memory.timestamp<15*60*1000) return memory.data;
    try  {
      const store=JSON.parse(sessionStorage.getItem(forecastCacheKey)||'{}');
      const saved=store[key];
      if(saved && Date.now()-saved.timestamp<15*60*1000) {
        forecastMemory.set(key,saved);
        return saved.data;
      }
    } catch(_)  {
    }
    return null;
  }

  function storeForecast(key,data)  {
    const entry= {
      timestamp:Date.now(),data
    };
    forecastMemory.set(key,entry);
    try  {
      const store=JSON.parse(sessionStorage.getItem(forecastCacheKey)||'{}'),now=Date.now();
      Object.keys(store).forEach(cacheKey=> {
        if(!store[cacheKey]||now-store[cacheKey].timestamp>=15*60*1000)delete store[cacheKey];
      });
      store[key]=entry;
      const keys=Object.keys(store);
      if(keys.length>60) keys.sort((a,b)=>store[a].timestamp-store[b].timestamp).slice(0,keys.length-60).forEach(cacheKey=>delete store[cacheKey]);
      sessionStorage.setItem(forecastCacheKey,JSON.stringify(store));
    } catch(_)  {
    }
  }

  async function loadModalWeather(lifecycle='quiet')  {
    if(!activeDate || modal.hidden) return;
    const coords=currentCoordinates(),date=activeDate;
    if(modalWeatherController) modalWeatherController.abort();
    const version=++modalWeatherVersion;
    if(lifecycle==='location') notify('loading','Updating location...');
    setModalDateLabel();
    if(!coords) {
      showModalNeedsLocation();
      return;
    }
    const location=resolvedLocation(coords);
    const offset=dateOffset(date);
    if(offset<0 || offset>16) {
      showModalNoData(location);
      if(lifecycle==='location')notify('success','Location updated');
      return;
    }
    const current=!weatherOverride || (Number(coords.latitude)===Number(state&&state.latitude)&&Number(coords.longitude)===Number(state&&state.longitude));
    if(date===localDateString() && current && state && Date.now()-Number(state.timestamp)<15*60*1000) {
      showModalWeather(state,location||state.location);
      if(lifecycle==='location')notify('success','Location updated');
      return;
    }
    const key=Number(coords.latitude).toFixed(6)+','+Number(coords.longitude).toFixed(6)+','+date;
    const cached=getForecastCache(key);
    if(cached) {
      cached.no_data?showModalNoData(location):showModalWeather(cached,location);
      if(lifecycle==='location')notify('success','Location updated');
      return;
    }
    showModalLoading(location);
    if(lifecycle==='open') notify('loading','Fetching weather...');
    modalWeatherController=new AbortController();
    const params=new URLSearchParams( {
      date:date,latitude:coords.latitude,longitude:coords.longitude
    });
    try  {
      const response=await fetch(modal.dataset.forecastUrl+'?'+params, {
        headers: {
          'X-Requested-With':'XMLHttpRequest'
        },signal:modalWeatherController.signal
      });
      const data=await response.json();
      if(!response.ok) throw new Error(data.error||'Weather forecast is unavailable.');
      if(version!==modalWeatherVersion || date!==activeDate) return;
      storeForecast(key,data);
      if(data.no_data) showModalNoData(location);
      else showModalWeather(data,location);
      if(lifecycle==='location') notify('success','Location updated');
      else if(lifecycle==='open') notify('success','Weather updated');
    } catch(error)  {
      if(error.name==='AbortError'||version!==modalWeatherVersion) return;
      showModalError(location,error.message);
      notify('error',lifecycle==='location'?'Failed to update location':'Failed to fetch weather');
    }
  }

  function renderLocationResults(locations)  {
    const list=$('modal-weather-search-results'),fragment=document.createDocumentFragment();
    lastSearchLocations=locations;
    locations.forEach((place,index)=> {
      const button=document.createElement('button');
      button.type='button';
      button.dataset.locationIndex=String(index);
      button.setAttribute('role','option');
      button.setAttribute('aria-selected','false');
      button.textContent=place.name;
      fragment.append(button);
    });
    list.replaceChildren(fragment);
  }

  async function searchLocations(query)  {
    if(modalSearchController) modalSearchController.abort();
    if(query.trim().length<2) {
      renderLocationResults([]);
      $('modal-weather-search-status').textContent='Enter at least 2 characters.';
      return;
    }
    modalSearchController=new AbortController();
    $('modal-weather-search-status').textContent='Searching...';
    const params=new URLSearchParams( {
      name:query.trim()
    });
    try  {
      const response=await fetch(modal.dataset.locationSearchUrl+'?'+params, {
        headers: {
          'X-Requested-With':'XMLHttpRequest'
        },signal:modalSearchController.signal
      });
      const data=await response.json();
      if(!response.ok) throw new Error(data.error||'Location search is unavailable.');
      renderLocationResults(data.locations||[]);
      $('modal-weather-search-status').textContent=data.locations?.length?'Choose a location.':'No locations found.';
    } catch(error)  {
      if(error.name==='AbortError') return;
      renderLocationResults([]);
      $('modal-weather-search-status').textContent='Location search is unavailable.';
      notify('error','Failed to search locations');
    }
  }

  async function chooseWeatherLocation(place)  {
    if(modalWeatherController) modalWeatherController.abort();
    weatherOverride= {
      name:place.name,latitude:Number(place.latitude),longitude:Number(place.longitude)
    };
    try {
      sessionStorage.setItem(weatherOverrideKey,JSON.stringify(weatherOverride))
    } catch(_) {
    }
    $('modal-weather-search-status').textContent='';
    renderLocationResults([]);
    await exitLocationSearch();
    if(!modal.hidden) loadModalWeather('location');
  }

  function useCurrentWeatherLocation()  {
    weatherOverride=null;
    try {
      sessionStorage.removeItem(weatherOverrideKey)
    } catch(_) {
    }
    $('modal-weather-search').hidden=true;
    $('modal-weather-search-input').setAttribute('aria-expanded','false');
    $('modal-weather-card').classList.remove('is-searching');
    $('modal-weather-change').focus();
    const coords=currentCoordinates();
    if(coords) loadModalWeather('location');
    else  {
      showModalNeedsLocation();
      $('weather-enable').click();
    }
  }
  
  function openLocationSearch()  {
    if(modalWeatherController) modalWeatherController.abort();
    modalWeatherVersion++;
    const search=$('modal-weather-search');
    search.classList.remove('is-exiting');
    search.classList.add('is-entering');
    search.hidden=false;
    $('modal-weather-card').classList.add('is-searching');
    const main=$('modal-weather-card').querySelector('.weather-widget-main');
    const actions=$('modal-weather-card').querySelector('.weather-widget-actions');
    main.inert=true;
    main.setAttribute('aria-hidden','true');
    actions.inert=true;
    actions.setAttribute('aria-hidden','true');
    $('modal-weather-search-input').setAttribute('aria-expanded','true');
    $('modal-weather-search-status').textContent='';
    requestAnimationFrame(()=> {
      search.classList.remove('is-entering');
      $('modal-weather-search-input').focus();
    });
  }

  function exitLocationSearch()  {
    const search=$('modal-weather-search');
    search.classList.remove('is-entering');
    search.classList.add('is-exiting');
    return new Promise(resolve=> {
      finishSearchTransition=resolve;
      searchTransitionTimer=setTimeout(()=> {
        search.hidden=true;
        search.classList.remove('is-exiting');
        $('modal-weather-card').classList.remove('is-searching');
        const main=$('modal-weather-card').querySelector('.weather-widget-main');
        const actions=$('modal-weather-card').querySelector('.weather-widget-actions');
        main.inert=false;
        main.removeAttribute('aria-hidden');
        actions.inert=false;
        actions.removeAttribute('aria-hidden');
        $('modal-weather-search-input').setAttribute('aria-expanded','false');
        if(!modal.hidden)$('modal-weather-change').focus();
        searchTransitionTimer=null;
        finishSearchTransition=null;
        resolve();
      },240);
    });
  }

  async function closeLocationSearch()  {
    await exitLocationSearch();
    if(!modal.hidden&&!weatherOverride) loadModalWeather('quiet');
  }

  function requestWeather(coords, manual=false, automatic=false)  {
    if(currentController) currentController.abort();
    currentController=new AbortController();
    renderWidgetLoading();
    if(manual) notify('loading','Fetching weather...');
    const params=new URLSearchParams( {
      latitude:coords.latitude,longitude:coords.longitude
    });
    fetch(`${widget.dataset.weatherUrl}?${params}`, {
      headers: {
        'X-Requested-With':'XMLHttpRequest'
      },signal:currentController.signal
    }).then(async response=> {
      const data=await response.json();
      if(!response.ok)throw new Error(data.error||'Failed to fetch weather');
      return data;
    }).then(data=> {
      data.timestamp=Date.now();
      data.latitude=coords.latitude;
      data.longitude=coords.longitude;
      renderWeather(data);
      if(manual)notify('success','Weather updated');
    }).catch(error=> {
      if(error.name==='AbortError')return;
      renderWidgetError('Check your connection or try again.');
      if(manual||automatic)notify('error','Failed to fetch weather');
    }).finally(()=> {
      currentController=null;
    });
  }

  function useCoordinates(coords, manual=false)  {
    try {
      sessionStorage.setItem('restylePlannerLocation',JSON.stringify(coords))
    } catch(_) {
    }
    requestWeather(coords,manual);
  }

  function askLocation(manual=true)  {
    if(!navigator.geolocation) {
      renderWidgetError('Location is not available in this browser.');
      return;
    }
    const button=$('weather-enable');
    button.className='btn btn--compact primary-btn weather-enable';
    button.disabled=true;
    button.setAttribute('aria-busy','true');
    button.textContent='Requesting location...';
    navigator.geolocation.getCurrentPosition(p=>useCoordinates( {
      latitude:p.coords.latitude,longitude:p.coords.longitude
    },manual),err=> {
      renderWidgetError(err.code===1?'Location permission denied':'Could not get your location.');
      if(err.code===1)notify('error','Location permission denied');
      else if(manual)notify('error','Failed to fetch weather');
    }, {
      enableHighAccuracy:false,timeout:12000,maximumAge:300000
    });
  }

  async function initWeather()  {
    state=readCached();
    if(state)renderWeather(state);
    const cached=readCached();
    if(cached && Date.now()-cached.timestamp<15*60*1000) {
      state=cached;
      window.plannerWeather=cached;
      window.dispatchEvent(new CustomEvent('weather:updated', {
        detail:cached
      }));
    }
    let permission='prompt';
    try {
      permission=(await navigator.permissions.query( {
        name:'geolocation'
      })).state
    } catch(_) {
    }
    if(permission==='granted')  {
      let coords=null;
      try {
        coords=JSON.parse(sessionStorage.getItem('restylePlannerLocation')||'null')
      } catch(_) {
      }
      if(coords) {
        if(!cached||Date.now()-cached.timestamp>=15*60*1000)requestWeather(coords,false,true);
      } else askLocation(false);
    }
    $('weather-enable').addEventListener('click',()=>askLocation(true));
    $('weather-refresh').addEventListener('click',()=> {
      let coords=null;
      try {
        coords=JSON.parse(sessionStorage.getItem('restylePlannerLocation')||'null')
      } catch(_) {
      }
      if(coords)requestWeather(coords,true);
      else askLocation(true);
    });
    refreshTimer=setInterval(()=> {
      if(document.hidden)return;
      let coords=null;
      try {
        coords=JSON.parse(sessionStorage.getItem('restylePlannerLocation')||'null')
      } catch(_) {
      }
      if(coords)requestWeather(coords,false,true)
    },15*60*1000);
    document.addEventListener('visibilitychange',()=> {
      if(document.hidden)return;
      const old=readCached();
      let coords=null;
      try {
        coords=JSON.parse(sessionStorage.getItem('restylePlannerLocation')||'null')
      } catch(_) {
      }
      if(coords&&(!old||Date.now()-old.timestamp>=15*60*1000))requestWeather(coords,false,true)
    });
  }

  function weatherChanged(next)  {
    state=next||null;
    if(activeDate&&!modal.hidden&&!weatherOverride&&!$('modal-weather-card').classList.contains('is-searching')) loadModalWeather('quiet');
  }

  function cardHTML(item)  {
    const template=document.createElement('template');
    template.innerHTML=item.html;
    const card=template.content.firstElementChild;
    if(card) {
      const button=card.querySelector('.mm-outfit-select');
      if(button) {
        button.setAttribute('aria-pressed',item.selected?'true':'false');
        button.classList.toggle('is-selected',!!item.selected);
      }
      card.classList.toggle('is-selected',!!item.selected);
    }
    return card;
  }

  let outfits=[], selectedId=null;

  function renderLists()  {
    const recommended=modalWeather&&!modalWeather.no_data?outfits.filter(o=>o.weather_key===modalWeather.category).sort((a,b)=>(a.status==='ready'?0:1)-(b.status==='ready'?0:1)).slice(0,3):[];
    const empty=$('planner-recommended-empty');
    empty.textContent=modalWeatherLoading?'Loading recommendations...':modalWeather?.no_data?'No matching outfits for this weather yet.':modalWeather?'No matching outfits for this weather yet.':'Allow location or search for a city to get recommendations.';
    empty.classList.toggle('is-loading',modalWeatherLoading);
    empty.setAttribute('aria-busy',modalWeatherLoading?'true':'false');
    const fill=(el,items,emptyId)=> {
      const f=document.createDocumentFragment();
      items.forEach(o=> {
        const card=cardHTML(o);
        if(card)f.append(card)
      });
      el.replaceChildren(f);
      $(emptyId).hidden=items.length>0
    };
    fill($('planner-recommended'),recommended,'planner-recommended-empty');
    fill($('planner-all-outfits'),outfits,'planner-all-empty');
  }

  async function loadOutfits()  {
    if(!activeDate)return;
    const url=new URL(modal.dataset.optionsUrl,location.origin);
    url.searchParams.set('date',activeDate);
    const response=await fetch(url, {
      headers: {
        'X-Requested-With':'XMLHttpRequest'
      }
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'Could not load outfits');
    outfits=data.outfits;
    selectedId=data.selected_id;
    outfits.forEach(o=>o.selected=o.id===selectedId);
    $('planner-dialog-date').textContent=fmtDate(activeDate);
    $('planner-add-outfit').href=`${modal.dataset.addUrl}?planner_return=${encodeURIComponent(activeDate)}`;
    $('planner-remove-unavailable-plan').hidden=!outfits.some(o=>o.id===selectedId&&o.status==='washing');
    renderLists();
  }

  function open(date)  {
    activeDate=date;
    previousFocus=document.activeElement;
    $('planner-dialog-date').textContent=fmtDate(date);
    $('modal-weather-search').hidden=true;
    $('modal-weather-search').classList.remove('is-entering','is-exiting');
    $('modal-weather-card').classList.remove('is-searching');
    $('modal-weather-search-input').setAttribute('aria-expanded','false');
    const main=$('modal-weather-card').querySelector('.weather-widget-main');
    const actions=$('modal-weather-card').querySelector('.weather-widget-actions');
    main.inert=false;
    main.removeAttribute('aria-hidden');
    actions.inert=false;
    actions.removeAttribute('aria-hidden');
    modal.hidden=false;
    document.body.classList.add('planner-modal-open');
    modal.querySelector('.mm-modal-close').focus();
    setModalDateLabel();
    loadModalWeather('open');
    loadOutfits().catch(e=>notify('error',e.message));
  }

  function close()  {
    modal.hidden=true;
    $('modal-weather-search').hidden=true;
    $('modal-weather-search').classList.remove('is-entering','is-exiting');
    $('modal-weather-card').classList.remove('is-searching');
    $('modal-weather-search-input').setAttribute('aria-expanded','false');
    const main=$('modal-weather-card').querySelector('.weather-widget-main');
    const actions=$('modal-weather-card').querySelector('.weather-widget-actions');
    main.inert=false;
    main.removeAttribute('aria-hidden');
    actions.inert=false;
    actions.removeAttribute('aria-hidden');
    if(searchTransitionTimer) {
      clearTimeout(searchTransitionTimer);
      searchTransitionTimer=null;
      finishSearchTransition?.();
      finishSearchTransition=null;
    }
    if(modalWeatherController)modalWeatherController.abort();
    if(modalSearchController)modalSearchController.abort();
    clearTimeout(modalSearchTimer);
    document.body.classList.remove('planner-modal-open');
    previousFocus?.focus();
  }

  async function post(url,body)  {
    const response=await fetch(url, {
      method:'POST',headers: {
        'Content-Type':'application/json','X-CSRFToken':token,'X-Requested-With':'XMLHttpRequest'
      },body:JSON.stringify(body)
    });
    let data= {
    };
    try {
      data=await response.json()
    } catch(_) {
    }
    if(!response.ok) {
      const error=new Error(data.error||`Request failed (${response.status})`);
      error.status=response.status;
      throw error
    }
    return data;
  }

  async function syncSlots()  {
    if(!grid)return;
    const url=new URL(grid.dataset.stateUrl,location.origin);
    url.searchParams.set('week',grid.dataset.weekStart);
    const response=await fetch(url, {
      headers: {
        'X-Requested-With':'XMLHttpRequest'
      }
    });
    const data=await response.json();
    if(!response.ok)throw new Error(data.error||'Could not update planner');
    data.slots.forEach(s=> {
      const slot=grid.querySelector(`.outfit-slot[data-date="${s.date}"]`);
      if(!slot)return;
      slot.dataset.planId=s.plan_id||'';
      slot.classList.toggle('has-plan',!!s.visible);
      slot.classList.toggle('is-unavailable',!!s.plan_id&&!s.visible);
      if(s.visible&&s.html) {
        const t=document.createElement('template');
        t.innerHTML=s.html;
        slot.replaceChildren(t.content.firstElementChild)
      } else {
        const b=document.createElement('button');
        b.type='button';
        b.className='planner-pick';
        b.dataset.openPlan=s.date;
        b.setAttribute('aria-label',`Pick outfit for ${fmtDate(s.date)}`);
        b.innerHTML='<svg viewBox="0 0 48 48" class="plus-icon" aria-hidden="true"><circle cx="24" cy="24" r="21" fill="none" stroke="currentColor" stroke-width="4"/><path d="M24 13v22M13 24h22" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg><span>Pick your outfit</span>';
        slot.replaceChildren(b)
      }
    });
  }

  async function removePlan()  {
    const had=!!selectedId;
    notify('loading',had?'Removing plan...':'Saving plan...');
    try {
      await post(modal.dataset.clearUrl, {
        date:activeDate
      });
      await syncSlots();
      selectedId=null;
      close();
      notify('success',had?'Plan removed':'Plan removed');
    } catch(e) {
      notify('error',e.message==='Request failed'?'Failed to remove plan':e.message)
    }
  }

  async function selectOutfit(id)  {
    const isSelected=selectedId!==null&&selectedId!==undefined&&Number(id)===Number(selectedId);
    const wasReplacing=selectedId!==null&&selectedId!==undefined&&!isSelected;
    const failure=isSelected?'Failed to remove plan':wasReplacing?'Failed to update plan':'Failed to save plan';
    notify('loading',isSelected?'Removing plan...':wasReplacing?'Updating plan...':'Saving plan...');
    try {
      if(isSelected)await post(modal.dataset.clearUrl, {
        date:activeDate
      });
      else await post(modal.dataset.saveUrl, {
        date:activeDate,outfit_id:id
      });
      await syncSlots();
      close();
      notify('success',isSelected?'Plan removed':wasReplacing?'Plan updated':`Outfit planned for ${fmtDate(activeDate)}`);
    } catch(e) {
      notify('error',e.message.toLowerCase().includes('wash')?'Some items are in the wash':e.status?e.message:failure);
    }
  }

  async function saveLaundry(form)  {
    notify('loading','Saving laundry days...');
    try {
      const response=await fetch(form.action, {
        method:'POST',headers: {
          'X-CSRFToken':token,'X-Requested-With':'XMLHttpRequest'
        },body:new FormData(form)
      });
      const data=await response.json();
      if(!response.ok)throw new Error(data.error||'Failed to save laundry days');
      await syncSlots();
      notify('success','Laundry days saved')
    } catch(_) {
      notify('error','Failed to save laundry days')
    }
  }

  grid?.addEventListener('click',e=> {
    const pick=e.target.closest('[data-open-plan]');
    const card=e.target.closest('[data-plan-date]');
    if(pick)open(pick.dataset.openPlan);
    else if(card)open(card.dataset.planDate)
  });

  modal.querySelector('.mm-modal-close').addEventListener('click',close);

  modal.addEventListener('click',e=> {
    if(e.target===modal)close()
  });

  modal.addEventListener('click',e=> {
    const button=e.target.closest('.mm-outfit-select');
    if(button&&!button.disabled)selectOutfit(button.dataset.outfitId)
  });

  $('modal-weather-change').addEventListener('click',openLocationSearch);
  $('modal-weather-search-back').addEventListener('click',closeLocationSearch);
  $('modal-weather-allow').addEventListener('click',()=> {
    showModalNeedsLocation();
    $('weather-enable').click();
  });
  $('modal-weather-use-current').addEventListener('click',useCurrentWeatherLocation);
  $('modal-weather-retry').addEventListener('click',()=>loadModalWeather('open'));
  $('modal-weather-search-input').addEventListener('input',event=> {
    clearTimeout(modalSearchTimer);
    const query=event.currentTarget.value;
    modalSearchTimer=setTimeout(()=>searchLocations(query),400);
  });

  $('modal-weather-search-input').addEventListener('keydown',event=> {
    if(event.key==='ArrowDown') {
      const first=$('modal-weather-search-results').querySelector('button');
      if(first) {
        event.preventDefault();
        first.focus();
      }
    } else if(event.key==='Escape')closeLocationSearch();
  });

  $('modal-weather-search-results').addEventListener('click',event=> {
    const button=event.target.closest('[data-location-index]');
    const place=button&&lastSearchLocations[Number(button.dataset.locationIndex)];
    if(place)chooseWeatherLocation(place);
  });

  $('planner-remove-unavailable-plan').addEventListener('click',()=>selectOutfit(selectedId));

  document.addEventListener('keydown',e=> {
    if(modal.hidden)return;
    if(e.key==='Escape') {
      close();
      return
    }
    if(e.key==='Tab') {
      const focus=[...dialog.querySelectorAll('a[href],button:not(:disabled),[tabindex]:not([tabindex="-1"])')].filter(x=>!x.closest('[hidden]'));
      if(!focus.length)return;
      if(e.shiftKey&&document.activeElement===focus[0]) {
        e.preventDefault();
        focus.at(-1).focus()
      } else if(!e.shiftKey&&document.activeElement===focus.at(-1)) {
        e.preventDefault();
        focus[0].focus()
      }
    }
  });

  document.getElementById('laundry-days-form')?.addEventListener('change',e=>saveLaundry(e.currentTarget));
  window.addEventListener('weather:updated',e=>weatherChanged(e.detail));
  window.addEventListener('message',e=> {
    if(e.origin!==location.origin||e.data?.type!=='planner-outfit-saved')return;
    if(activeDate&&!modal.hidden)loadOutfits().catch(err=>notify('error',err.message));
    else open(new URLSearchParams(location.search).get('choose_date')||new Date().toISOString().slice(0,10));
  });
  const params=new URLSearchParams(location.search);
  if(params.get('planner_saved')==='1'&&window.opener) {
    window.opener.postMessage( {
      type:'planner-outfit-saved'
    },location.origin);
    window.close()
  }
  initWeather();
  if(params.has('choose_date'))open(params.get('choose_date'));
  window.addEventListener('pagehide',()=>{clearInterval(refreshTimer);clearInterval(todayRefreshTimer)});
})();
