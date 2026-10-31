"""IMU 姿态融合原型 — deterministic numerical prototype."""
import argparse,json
from pathlib import Path
import numpy as np

def finite(a,ndim=None):
 a=np.asarray(a,dtype=float)
 if not np.isfinite(a).all() or not a.size or (ndim is not None and a.ndim!=ndim): raise ValueError('Invalid shape, empty or nonfinite input')
 return a
def process(gyro,accel,dt=.01,alpha=.98):
 gyro=finite(gyro,1);accel=finite(accel,2)
 if accel.shape!=(len(gyro),3) or dt<=0 or not 0<=alpha<=1:raise ValueError('Invalid IMU input')
 if np.any(np.linalg.norm(accel,axis=1)<1e-9):raise ValueError('Zero acceleration vector')
 angle=float(np.arctan2(accel[0,1],accel[0,2]));out=[]
 for rate,a in zip(gyro,accel):
  predicted=angle+rate*dt;measured=np.arctan2(a[1],a[2]);delta=np.arctan2(np.sin(measured-predicted),np.cos(measured-predicted));angle=predicted+(1-alpha)*delta;out.append(angle)
 return np.unwrap(out)

def demo():
 rng=np.random.default_rng(42);x=np.arange(1500)*.01;truth=.4*np.sin(x*.7);gyro=np.gradient(truth,.01)+.025+rng.normal(0,.015,len(x));accel=np.column_stack([np.zeros(len(x)),np.sin(truth),np.cos(truth)])+rng.normal(0,.015,(len(x),3))
 out=process(gyro,accel);rmse=float(np.sqrt(np.mean((out-truth)**2)));assert rmse<.03
 return x,{'True roll rad':truth,'Fused roll rad':out,'Gyro integration rad':np.cumsum(gyro)*.01},{'roll_rmse_rad':rmse}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=Path('artifacts'));args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 x,series,metrics=demo()
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 if x is None:
  fig,axes=plt.subplots(1,len(series),figsize=(14,4),layout='constrained');axes=np.atleast_1d(axes)
  for ax,(label,values) in zip(axes,series.items()):ax.imshow(values,cmap='viridis');ax.set_title(label);ax.set_axis_off()
 else:
  fig,ax=plt.subplots(figsize=(11,5),layout='constrained')
  for label,values in series.items():ax.plot(x,values,label=label)
  ax.legend();ax.grid(alpha=.2)
 fig.suptitle('Synthetic prototype validation — not field measurements')
 fig.savefig(args.output/'result.png',dpi=140);plt.close(fig)
 np.savez_compressed(args.output/'results.npz',**{str(i):v for i,v in enumerate(series.values())})
 (args.output/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics,indent=2))
if __name__=='__main__':main()
