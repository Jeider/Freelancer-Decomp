// Three real Omega-15 models, same material and pose with relief off/on.
p->ExRockNormalsPrepare();R(e->RockDetail&&e->bRockEnabled,"shared runtime relief map available");
R(fabsf(e->RockDetailStrength-2.4f)<.001f&&fabsf(e->RockMacroStrength-3.f)<.001f,"installed relief strengths retained");
const float relief=e->RockDetailStrength,macro=e->RockMacroStrength;
rs(D3DRS_ZENABLE,1);rs(D3DRS_ZWRITEENABLE,1);rs(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);rs(D3DRS_FOGENABLE,0);
mat.Diffuse={1,1,1,1};mat.Ambient={1,1,1,1};C(p->SetMaterial(&mat));
e->SurfaceShader=RPSurfaceRock;
const DWORD bg=0xff101820;
auto pixels=[&](){C(d->GetRenderTargetData(target,read));C(read->LockRect(&lock,0,D3DLOCK_READONLY));
 std::vector<DWORD> result(900*600);for(int y=0;y<600;++y)memcpy(result.data()+y*900,(char*)lock.pBits+y*lock.Pitch,3600);
 read->UnlockRect();return result;};
C(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,bg,1,0));
for(int model=0;model<3;++model){
 char letter=char('a'+model);std::string path=std::string(MESH_DIR)+letter;
 char modelPath[100];sprintf_s(modelPath,"SOLAR/ASTEROIDS_MOD/om15/ast_o15_nrml_%c.3db",letter);
 R(RockNormalSolarModel(modelPath)&&!RockNormalExcludedModel(modelPath),"native solar opens rock-normal scope");
 unsigned count=0;std::ifstream f(path+".bin",std::ios::binary);f.read((char*)&count,4);
 std::vector<V> vertices(count);f.read((char*)vertices.data(),count*sizeof(V));R(f.good()&&count>500,"installed model loaded");
 float radius=0;for(auto const& v:vertices)radius=(std::max)(radius,sqrtf(v.x*v.x+v.y*v.y+v.z*v.z));
 base.Texture->Release();C(D3DXCreateTextureFromFileA(d,(path+".texture").c_str(),&base.Texture));
 p->DeviceStates_.TextureBindings[0]={&base,1,{}};C(d->SetTexture(0,base.Texture));
 D3DXVECTOR3 eye(radius*1.6f,radius*.7f,-radius*3),centre(0,0,0),up(0,1,0);D3DXMATRIX view,projection;
 D3DXMatrixLookAtLH(&view,&eye,&centre,&up);D3DXMatrixPerspectiveFovLH(&projection,.85f,1,1,10000);
 memcpy(p->Transforms_.View.Values,&view,64);memcpy(p->Transforms_.Projection.Values,&projection,64);
 C(d->SetTransform(D3DTS_VIEW,&view));C(d->SetTransform(D3DTS_PROJECTION,&projection));
 C(p->SetRockNormalScope(RPRockAsteroid,radius));R(e->RockClass==RPRockAsteroid,"IRPRockNormals scope enabled");
 auto draw=[&](unsigned flags){
  p->ExSurfaceRelease();C(p->SetLocalShadowReceiver(flags));C(d->SetFVF(fvf));C(d->BeginScene());
  R(p->ExSurfaceBegin(),"native physical material selected");
  C(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,count/3,vertices.data(),sizeof(V)));p->ExSurfaceEnd();C(d->EndScene());
 };
 D3DVIEWPORT9 vp={DWORD(model*300),0,300,300,0,1};C(d->SetViewport(&vp));
 e->RockDetailStrength=e->RockMacroStrength=0;draw(0);
 vp.Y=300;C(d->SetViewport(&vp));e->RockDetailStrength=relief;e->RockMacroStrength=macro;draw(0);
 auto frame=pixels();unsigned covered=0,changed=0;double difference=0;
 for(int y=0;y<300;++y)for(int x=model*300;x<(model+1)*300;++x){auto a=frame[y*900+x],b=frame[(y+300)*900+x];
  if(a==bg)continue;++covered;int error=delta(a,b);changed+=error>3;difference+=error;}
 printf("PASS model %c: %u covered, %u relief-changed pixels, mean RGB delta %.2f/255\n",letter,covered,changed,difference/(std::max)(1u,covered));
 R(covered>3000&&changed>covered/4&&difference/covered>2,"relief visibly changes native rock surface");
 float constants[16]={};C(d->GetPixelShaderConstantF(102,constants,4));
 R(fabsf(constants[0]-relief)<.001f&&fabsf(constants[4]-macro)<.001f&&fabsf(constants[6]-radius)<.001f,"real rock constants uploaded");
 IDirect3DBaseTexture9* detail=nullptr;C(d->GetTexture(13,&detail));R(detail==e->RockDetail,"real relief sampler bound");if(detail)detail->Release();
 // Scope state, including fog and distant native tier, must survive the handoff.
 rs(D3DRS_FOGENABLE,1);rs(D3DRS_FOGSTART,bits(1000));rs(D3DRS_FOGEND,bits(2000));draw(512|2048);
 float fog[4]={};C(d->GetPixelShaderConstantF(107,fog,1));R(fog[2]==0,"near fog retains enhanced material");
 draw(768|2048);C(d->GetPixelShaderConstantF(107,fog,1));R(fog[2]==1,"distant fog uses existing inexpensive tier");
 rs(D3DRS_FOGENABLE,0);draw(0);C(p->SetRockNormalScope(RPRockOff,0));
}
C(D3DXSaveSurfaceToFileA(argv[1],D3DXIFF_PNG,target,nullptr,nullptr));
puts("PASS real RP9 relief on all three native solar models; fog and distant tier; no game launch");return 0;
