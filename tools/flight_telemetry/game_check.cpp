int wmain(int argc, wchar_t** argv) {
    using namespace FlightTelemetry;
    assert(argc==2);
    std::wstring folder=argv[1];
    auto path=[&](wchar_t const* name){return folder+L"/"+name;};
    fixturePlayer.velocity={10,0,0};
    fixtureTarget.id=2; fixtureTarget.position={0,0,-100};fixtureTarget.velocity={0,0,20};
    fixtureTarget.shieldKnown=false;fixturePlayer.target=&fixtureTarget;
    Watchable contact{&fixtureTarget};fixtureScanner.Scans.Count=1;fixtureScanner.Scans.Entries[0].value=&contact;
    // Dormant hooks must not touch output files even with full combat data.
    BeginFrame(.1f,false);EndFrame(false);Input(120,1,true,false,0);
    Steering("mouse",1,0,0);Command("throttle",1);Shot(1,9,false,nullptr);Damage(1,DamageList());
    assert(!IsRecording());
    fixturePresent=false;
    assert(!Start(path(L"no_ship.jsonl").c_str()));
    assert(std::string(LastError())=="not_in_space");
    fixturePresent=true;
    assert(Start(path(L"adapter.jsonl").c_str()));
    Input(120,1,true,false,0);Input(120,1,false,false,0);
    {
        OriginScope mapped(Origin::MappedInput);
        Command("engage_engine",0);
        {OriginScope nested(Origin::Synthetic);Command("cruise",0);}
        Command("afterburner",1);
    }
    Command("unknown_command",1);
    Steering("mouse",.2f,.3f,0);
    Shot(2,9,false,nullptr); // Other ship must not be labelled as the player's shot.
    Shot(1,9,false,nullptr);Shot(1,10,true,&fixtureTarget.position);
    Damage(1,DamageList());
    Collision(1,2,1,7,fixtureTarget.position,{0,0,1},{0,0,-20});
    BeginFrame(1.f/30,false);EndFrame(false);
    fixturePaused=true;BeginFrame(2,true);EndFrame(false);
    BeginFrame(2,true);EndFrame(false); // No invented paused snapshots.
    fixtureInput=false;BeginFrame(2,true);EndFrame(false);
    fixtureInput=true;BeginFrame(2,true);EndFrame(false);
    fixturePaused=false;BeginFrame(1.f/30,false);EndFrame(false);
    ++fixtureRevision;
    BeginFrame(.1f,false);
    assert(!IsRecording() && Stop());

    assert(Start(path(L"system_change.jsonl").c_str()));
    ++fixtureSystem;Input(120,1,true,false,0);
    assert(!IsRecording());
    assert(Start(path(L"ship_loss.jsonl").c_str()));
    fixturePresent=false;EndFrame(false);
    assert(!IsRecording());fixturePresent=true;
    puts("PASS: adapter snapshots, target/energy, command origins, shots/damage, pause/focus, load/system/ship boundaries");
}
