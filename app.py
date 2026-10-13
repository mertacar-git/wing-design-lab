import json
from dataclasses import asdict,replace
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from core import Wing,geometry,polar,performance,planform,naca4

st.set_page_config(page_title='Wing Design Lab',page_icon='🪽',layout='wide')
st.title('Wing Design Lab')
st.caption('Trapezoidal geometry · analytical finite-wing estimates · NACA profiles')
span=st.sidebar.slider('Span (m)',0.5,5.0,2.0)
root=st.sidebar.slider('Root chord (m)',0.1,1.0,0.35)
taper=st.sidebar.slider('Taper ratio',0.1,1.0,0.6)
sweep=st.sidebar.slider('Leading-edge sweep (degrees)',-10.0,45.0,0.0)
eff=st.sidebar.slider('Assumed efficiency e',0.3,1.0,0.8)
cd0=st.sidebar.number_input('Assumed CD0',0.001,0.2,0.025,0.001)
clmax=st.sidebar.slider('Assumed CLmax',0.5,2.0,1.2)
mass=st.sidebar.number_input('Aircraft mass (kg)',0.1,100.0,2.0,0.1)
speed=st.sidebar.slider('Airspeed (m/s)',5.0,60.0,20.0)
code=st.sidebar.text_input('NACA four-digit profile','2412')
wing=Wing(span,root,taper,sweep,eff,cd0,clmax)
try:
    stats=performance(wing,mass,speed); section=naca4(code)
except ValueError as exc: st.error(str(exc)); st.stop()
cols=st.columns(4)
for col,label,value in zip(cols,['Area','Aspect ratio','Estimated stall speed','Required alpha'],[f'{stats["area_m2"]:.3f} m²',f'{stats["aspect_ratio"]:.2f}',f'{stats["estimated_stall_speed_ms"]:.1f} m/s',f'{stats["required_alpha_deg"]:.1f}°']): col.metric(label,value)
if not stats['feasible_by_cl_limit']: st.warning('Required CL exceeds the assumed CLmax. The selected flight condition is outside this model’s feasible lift range.')
tabs=st.tabs(['Geometry','Polar comparison','Span sweep','Export'])
with tabs[0]:
    coords=planform(wing)
    figure=go.Figure(go.Scatter(x=[p[0] for p in coords],y=[p[1] for p in coords],fill='toself',name='Planform')); figure.update_yaxes(scaleanchor='x'); st.plotly_chart(figure,width='stretch')
    figure=go.Figure()
    for side in ['upper','lower']: figure.add_scatter(x=[p[0] for p in section[side]],y=[p[1] for p in section[side]],name=side)
    figure.update_yaxes(scaleanchor='x'); st.plotly_chart(figure,width='stretch')
    st.caption('NACA shape is a geometry export. It is not used to infer CD0, CLmax or zero-lift angle.')
with tabs[1]:
    comparison=replace(wing,taper=1.0,span_m=span*0.8)
    rows=[dict(design=label,**polar(w,alpha,speed)) for label,w in [('Selected',wing),('Short rectangular baseline',comparison)] for alpha in range(-5,16)]
    data=pd.DataFrame(rows)
    import plotly.express as px
    st.plotly_chart(px.line(data,x='alpha_deg',y='cl',color='design'),width='stretch')
    st.plotly_chart(px.line(data,x='cd',y='cl',color='design'),width='stretch')
    st.caption('Linear estimates beyond CLmax are marked in exports and must not be treated as post-stall predictions.')
with tabs[2]:
    scan=pd.DataFrame([dict(span_m=round(s,2),**performance(replace(wing,span_m=s),mass,speed)) for s in [0.5+i*0.1 for i in range(46)]])
    st.plotly_chart(px.line(scan,x='span_m',y='required_alpha_deg'),width='stretch'); st.dataframe(scan,width='stretch')
with tabs[3]:
    st.download_button('Design JSON',json.dumps(dict(wing=asdict(wing),performance=stats,naca=code),indent=2),'wing.json','application/json')
    st.download_button('Polar CSV',data.to_csv(index=False),'polar.csv','text/csv')
    st.download_button('Span sweep CSV',scan.to_csv(index=False),'span_sweep.csv','text/csv')
    profile=pd.DataFrame([dict(surface=side,x_c=x,y_c=y) for side in ['upper','lower'] for x,y in section[side]])
    st.download_button('Airfoil coordinates CSV',profile.to_csv(index=False),'airfoil.csv','text/csv')
st.info('Low-speed analytical model, not CFD or VSPAERO. It assumes small angles, a supplied efficiency factor and supplied profile-drag/lift-limit values. Sweep correction is approximate. Structural weight, Reynolds effects and spanwise loading are not computed.')
