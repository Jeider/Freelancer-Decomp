int main() {
    using namespace PlayerActionStats;
    using namespace ServerActionStats;
    Players.players[2].client_id=2;
    State initial;initial.Set(Counter::InertiaSeconds,999.75);
    Load(1,initial);Load(2,State());
    Bridge packet;assert(PlayerActionStatsBridge(&packet));auto firstEpoch=packet.epoch;
    packet.operation=1;packet.state.Add(Counter::InertiaSeconds,.25);
    packet.state.Set(Counter::Kills,999);assert(PlayerActionStatsBridge(&packet));
    assert(packet.state.Get(Counter::InertiaSeconds)==1000 && packet.state.Get(Counter::Kills)==0);
    assert(PlayerActionStatsBridge(&packet)); // Repeated totals are idempotent.
    assert(Snapshot(1).Get(Counter::InertiaSeconds)==1000);
    packet.state.Set(Counter::InertiaSeconds,999);assert(!PlayerActionStatsBridge(&packet));
    assert(Snapshot(1).Get(Counter::InertiaSeconds)==1000);
    Load(1,initial);assert(!PlayerActionStatsBridge(&packet)); // Stale save epoch.
    packet={};assert(PlayerActionStatsBridge(&packet));assert(packet.epoch!=firstEpoch);
    assert(Snapshot(1).Get(Counter::InertiaSeconds)==999.75 && Snapshot(2).Get(Counter::InertiaSeconds)==0);
    Landed(1);assert(Snapshot(1).Get(Counter::Landings)==0); // Loading a docked save isn't landing.
    EnteredSpace(1,true);EnteredSpace(1,true);Landed(1);Landed(1);
    assert(Snapshot(1).Get(Counter::Launches)==1 && Snapshot(1).Get(Counter::Landings)==1);
    auto& p=Players[1];p.equipment.Items={{10,7,5}};
    BeginTrade(1,50,2,true);InventoryChanged(p);
    assert(Snapshot(1).Get(Counter::BuyTransactions)==0);
    p.equipment.Items[0].Count+=2;InventoryChanged(p);
    assert(Snapshot(1).Get(Counter::BuyTransactions)==0);
    p.cash-=100;CashChanged(p,p.cash+100);InventoryChanged(p);
    assert(Snapshot(1).Get(Counter::BuyTransactions)==1 && Snapshot(1).Get(Counter::UnitsBought)==2);
    assert(Snapshot(1).Get(Counter::CreditsSpent)==100);
    // Native sell order is cash -> market request -> inventory removal.
    p.cash+=70;CashChanged(p,p.cash-70);BeginTrade(1,50,1,false);
    p.equipment.Items[0].Count-=1;InventoryChanged(p);InventoryChanged(p);
    assert(Snapshot(1).Get(Counter::SellTransactions)==1 && Snapshot(1).Get(Counter::CreditsReceived)==70);
    BeginTrade(1,50,1,true);Landed(1);p.cash-=50;CashChanged(p,p.cash+50);
    p.equipment.Items[0].Count+=1;InventoryChanged(p);
    assert(Snapshot(1).Get(Counter::BuyTransactions)==1);
    UsedItem(p,7,2);assert(Snapshot(1).Get(Counter::Nanobots)==2);
    Visited(1,10);Visited(1,20);
    assert(Snapshot(1).Get(Counter::Discoveries)==2 && Snapshot(1).Get(Counter::SystemsDiscovered)==1);
    GameObject victim;victim.id=102;victim.object.OwnerPlayer=2;
    GameObject ally;ally.id=300;ally.attitude=1;victim.target=&ally;
    DamageList damage;damage.attacker=1;damage.destroyed=true;
    damage.Entries={{7,DamageEntry::SubObjFate::Destroyed}};
    Damaged(&victim,damage);Damaged(&victim,damage);
    assert(Snapshot(1).Get(Counter::EnemyWeaponsDisabled)==1 && Snapshot(2).Get(Counter::Deaths)==1);
    assert(Snapshot(1).Get(Counter::DamageDealtEvents)==2);
    assert(Snapshot(1).Get(Counter::AllyAttackersDestroyed)==1);
    FILE* file=nullptr;assert(fopen_s(&file,"roundtrip.ini","wb")==0);
    Save(file,Snapshot(1));assert(fclose(file)==0);
    auto saved=Snapshot(1);Load(1,State());assert(Snapshot(1).Get(Counter::InertiaSeconds)==0);
    Load(1,saved);assert(Snapshot(1).Get(Counter::InertiaSeconds)==999.75);
    Clear(1);packet={};assert(!PlayerActionStatsBridge(&packet));
    puts("PASS: save isolation/rollback, epoch rejection, monotonic/idempotent totals, server ownership, confirmed trade, consumables, landing/load guards, damage dedup");
}
