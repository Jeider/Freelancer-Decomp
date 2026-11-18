#pragma once
bool TrainCourierCanStart(unsigned base);
class INI_Reader;
void TrainCourierOnPlayerLoad(unsigned player,INI_Reader* reader);
void TrainCourierAccessDenied(unsigned player);
bool TrainCourierCanReboard(unsigned player,unsigned target);
