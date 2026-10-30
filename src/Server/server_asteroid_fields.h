#pragma once
class StarSystem;
class Vector;
void OnServerAsteroidKilled(StarSystem& system, unsigned id, Vector const& position);
void LoadServerAsteroidFields(StarSystem& system);
void UpdateServerAsteroidFields(StarSystem& system, float dt);
void UnloadServerAsteroidFields(StarSystem& system);
float ServerAsteroidViewRadius(StarSystem& system);
