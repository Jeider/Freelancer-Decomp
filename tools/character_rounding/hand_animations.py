"""Decode the native hand ANM channels and evaluate their sphere joints offline.

Matches EngBase ChannelDecompressFrames (0x40 xyz/w>=0) and ApplySphereJoint.
"""
import gzip
import json
import math
import struct
import numpy as np


def quat_matrix(q):
    w,x,y,z=np.asarray(q)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])


def decode(channel):
    from contours import blob
    count,rate,flags=struct.unpack('<IfI',blob(channel,'Header'));raw=blob(channel,'Frames');at=0;result=[]
    assert flags in (4,32,64,128,256),hex(flags)
    for i in range(count):
        if rate<0:t=struct.unpack_from('<f',raw,at)[0];at+=4
        else:t=i*rate
        if flags==4:q=struct.unpack_from('<4f',raw,at);at+=16
        elif flags==32:q=(1,0,0,0)
        elif flags in (64,128):
            v=np.array(struct.unpack_from('<3h',raw,at),dtype=float)/32767;at+=6
            if flags==64:q=np.r_[math.sqrt(max(0,1-np.dot(v,v))),v]
            else:
                n=np.linalg.norm(v);theta=n*math.pi*.5
                q=np.r_[math.cos(theta),v*(math.sin(theta)/n if n else 1)]
        else:q=np.array(struct.unpack_from('<4h',raw,at),dtype=float)/32767;at+=8
        result.append([float(t),list(map(float,q))])
    assert at==len(raw),(flags,at,len(raw))
    return result


def sample(frames,time):
    if time<=frames[0][0]:return np.array(frames[0][1])
    if time>=frames[-1][0]:return np.array(frames[-1][1])
    for (a,qa),(b,qb) in zip(frames,frames[1:]):
        if a<=time<=b:
            qa=np.array(qa);qb=np.array(qb)
            if qa@qb<0:qb=-qb
            dot=min(1.,max(-1.,qa@qb));u=(time-a)/(b-a)
            if dot>.9995:q=qa*(1-u)+qb*u
            else:
                theta=math.acos(dot);q=(qa*math.sin((1-u)*theta)+qb*math.sin(u*theta))/math.sin(theta)
            return q/np.linalg.norm(q)


def bindings(data):
    out=[]
    for b in data['bones']:
        a=np.array(b['native_bind']);M=np.eye(4);M[:3,:3]=a[:9].reshape(3,3);M[:3,3]=a[9:];out.append(np.linalg.inv(M))
    return out


def pose(data,clip,time):
    bind=bindings(data);ids={b['name']:i for i,b in enumerate(data['bones'])};world={}
    def at(i):
        if i in world:return world[i]
        b=data['bones'][i];parent=ids.get(b['parent']);B=bind[i]
        if parent is None:M=B.copy()
        else:
            local=np.linalg.inv(bind[parent])@B
            frames=clip.get(b['name'])
            if frames:local[:3,:3]=quat_matrix(sample(frames,time))@local[:3,:3]
            M=at(parent)@local
        world[i]=M;return M
    return [at(i) for i in range(len(bind))]


def skin(data,world):
    bind=bindings(data);transforms=[w@np.linalg.inv(b) for w,b in zip(world,bind)]
    p=np.c_[np.array(data['points']),np.ones(len(data['points']))];out=np.zeros((len(p),3))
    for b,M in enumerate(transforms):
        weights=np.array([w.get(str(b),0) for w in data['skin']])
        out+=(p@M.T)[:,:3]*weights[:,None]
    return out


def main():
    from contours import GAME, read_tree, child, blob, save_json
    from hands import OUT
    for sex in ('male','female'):
        r=read_tree((GAME/'DATA/CHARACTERS/ANIMATIONS'/('hand'+sex+'.anm')).read_bytes())[1][0]
        scripts=child(child(r,'Animation'),'Script');clips={}
        for script in scripts.children:
            clips[script.name]={blob(n,'Child name').rstrip(b'\0').decode():decode(child(n,'Channel')) for n in script.children if n.name.startswith('Joint map')}
        save_json(OUT/('animations_'+sex+'.json.gz'),clips)
        print(sex,len(clips),'native clips decoded')


if __name__=='__main__':main()
