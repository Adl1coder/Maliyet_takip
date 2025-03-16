class Parca:
    def __init__(self, ad, tur, maliyet):
        """
        Parça sınıfı, her parçanın adını, türünü ve maliyetini saklar.

        :param ad: Parçanın adı (str)
        :param tur: Parçanın türü (örneğin: "Buton", "Sensör") (str)
        :param maliyet: Parçanın maliyeti (float)
        """
        self.ad = ad
        self.tur = tur
        self.maliyet = maliyet

class Mouse:
    def __init__(self):
        """
        Mouse sınıfı, parçaları ve toplam maliyeti takip eder.
        """
        self.parcalar = []  # Eklenen parçaları saklayan liste
        self.toplam_maliyet = 0  # Başlangıçta maliyet sıfır

    def parca_ekle(self, parca):
        """
        Fareye yeni bir parça ekler ve maliyeti günceller.

        :param parca: Eklenen Parca nesnesi
        """
        self.parcalar.append(parca)
        self.toplam_maliyet += parca.maliyet
        print(f"{parca.ad} eklendi! Güncel toplam maliyet: {self.toplam_maliyet} TL")

    def maliyet_goruntule(self):
        """
        Mevcut maliyet durumunu listeler.
        """
        print("\nMevcut Parçalar ve Maliyetler:")
        for parca in self.parcalar:
            print(f"- {parca.ad} ({parca.tur}): {parca.maliyet} TL")
        print(f"Toplam Maliyet: {self.toplam_maliyet} TL\n")
