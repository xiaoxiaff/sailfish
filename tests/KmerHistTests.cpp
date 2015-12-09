#include "KmerDist.hpp"

// from http://stackoverflow.com/questions/2380962/generate-all-combinations-of-arbitrary-alphabet-up-to-arbitrary-length
std::vector<std::string> getAllWords(int length) {

    int N_LETTERS = 4;
    char alphabet[] = {'A', 'C', 'G', 'T'};
  std::vector<int> index(length, 0);
  std::vector<std::string> words;

  while(true)
  {
    std::string word(length, ' ');
    for (int i = 0; i < length; ++i)
      word[i] = alphabet[index[i]];
    words.push_back(word);

    for (int i = length-1; ; --i)
    {
      if (i < 0) return words;
      index[i]++;
      if (index[i] == N_LETTERS)
        index[i] = 0;
      else
        break;
    }
  }
}


SCENARIO("Kmer histogram encodes and decodes k-mers correctly") {

    GIVEN("All 6-mers") {
        std::vector<std::string> kmers = getAllWords(6);
        KmerDist<6> kh;
        for (auto& k : kmers) {
            auto i = kh.indexForKmer(k.c_str());
            auto kp = kh.kmerForIndex(i);
            WHEN("kmer is [" + k + "]") {
                THEN("decodes as [" + kp + "]") {
                    REQUIRE(k == kp);
                }
            }
        }
    }
}