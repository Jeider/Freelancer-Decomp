#pragma once
#include <algorithm>
#include <random>
#include <string>
#include <vector>

// One bag per player/dialogue/pool. First encounter uses the authored first line.
struct RpgFragmentRotation {
    std::vector<std::string> Bag;
    std::string Last;
    std::mt19937 Random{0x525047};
    std::string Next(std::vector<std::string> const& Pool) {
        if (Pool.empty()) return {};
        if (Bag.empty()) {
            Bag = Pool;
            std::shuffle(Bag.begin(), Bag.end(), Random);
            auto First = std::find(Bag.begin(), Bag.end(), Pool.front());
            if (Last.empty()) std::iter_swap(First, Bag.end() - 1);
            else if (Bag.size() > 1 && Bag.back() == Last)
                std::iter_swap(Bag.begin(), Bag.end() - 1);
        }
        Last = Bag.back(); Bag.pop_back();
        return Last;
    }
};
