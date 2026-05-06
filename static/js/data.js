/**
 * NEXUS — Product Data
 * Shared across all pages
 */

const PRODUCTS = (window.__CATALOG_DATA__ && window.__CATALOG_DATA__.products) || [
  {
    id: 1, name: "AirPods Pro 2", brand: "Apple", category: "Elektronika",
    subcategory: "Quloqchinlar",
    price: 349000, oldPrice: 429000, rating: 4.9, reviews: 2341, stock: 12,
    badge: "Bestseller", colors: ["#1a1a1a","#f5f5f0","#c8a882"], sizes: [],
    img: "electronics-airpods",
    desc: "AirPods Pro 2 — Apple ning eng ilgor simsiz quloqchinlari. Faol shovqin bloklovchi, Spatial Audio va H2 chip bilan jihozlangan. 30 soatgacha batareya hayoti.",
    features: ["H2 chip", "Faol shovqin bloklash", "Spatial Audio", "Suv chidamli IPX4", "6 soat tinglash"],
  },
  {
    id: 2, name: "Ultra Runner 5", brand: "Nike", category: "Sport",
    subcategory: "Sport Oyoq Kiyimi",
    price: 189000, oldPrice: null, rating: 4.7, reviews: 876, stock: 5,
    badge: "Yangi", colors: ["#0057d9","#ff4433","#1a1a1a"], sizes: ["39","40","41","42","43","44"],
    img: "sport-shoes",
    desc: "Yugurishga moljallangan yuqori texnologiyali krossovka. ZoomX kopigi va React platformasi bilan maksimal qulaylik va tezlik.",
    features: ["ZoomX kopik", "React platforma", "Flyknit yuqori qismi", "Rubber taglik", "Yengil 220g"],
  },
  {
    id: 3, name: "Minimalist Tee", brand: "Zara", category: "Kiyim",
    subcategory: "Futbolkalar",
    price: 49000, oldPrice: 79000, rating: 4.5, reviews: 543, stock: 30,
    badge: null, colors: ["#f5f5f0","#1a1a1a","#8b7355"], sizes: ["XS","S","M","L","XL"],
    img: "clothing-tee",
    desc: "100% organik paxta. Minimal dizayn, maksimal qulaylik. Har qanday uslub bilan uygunlashadi.",
    features: ["100% organik paxta", "Regular fit", "Ekologik boyoqlar", "Mashina yuvish mumkin", "180g/m2"],
  },
  {
    id: 4, name: "Galaxy S25 Ultra", brand: "Samsung", category: "Elektronika",
    subcategory: "Telefonlar",
    price: 1299000, oldPrice: null, rating: 4.8, reviews: 1204, stock: 8,
    badge: "Yangi", colors: ["#1a1a1a","#2d4a6e","#8b7355"], sizes: [],
    img: "electronics-phone",
    desc: "Samsung ning eng kuchli smartfoni. Snapdragon 8 Elite, 200MP kamera, S Pen va 5000mAh batareya.",
    features: ["Snapdragon 8 Elite", "200MP asosiy kamera", "S Pen kiritilgan", "5000mAh / 45W", "6.9\" Dynamic AMOLED"],
  },
  {
    id: 5, name: "Linen Sofa Set", brand: "IKEA", category: "Uy va Bog",
    subcategory: "Mebel",
    price: 2450000, oldPrice: 2990000, rating: 4.6, reviews: 328, stock: 3,
    badge: "Chegirma", colors: ["#d4c5a9","#8b7355","#4a5568"], sizes: [],
    img: "home-sofa",
    desc: "Skandinaviya uslubidagi zamonaviy divan toplami. Tabiiy kanop mato, qattiq yogoch oyoqlar. 3+2 orindiq.",
    features: ["Tabiiy kanop mato", "Qarogay oyoqlar", "3+2 konfiguratsiya", "Olinadigan yostiqlar", "10 yil kafolat"],
  },
  {
    id: 6, name: "Retinol Night Cream", brand: "The Ordinary", category: "Gozallik",
    subcategory: "Parvarish",
    price: 89000, oldPrice: null, rating: 4.4, reviews: 721, stock: 20,
    badge: null, colors: ["#f5f0e8"], sizes: [],
    img: "beauty-cream",
    desc: "0.5% Retinol va B5 vitamini. Terini qayta tiklaydi, mayda ajinlarni kamaytiradi. Klinikalik sinovdan otgan formula.",
    features: ["0.5% Retinol", "Vitamin B5", "Hyaluronic Acid", "Paraben-free", "50ml"],
  },
  {
    id: 7, name: "MacBook Air M4", brand: "Apple", category: "Elektronika",
    subcategory: "Kompyuterlar",
    price: 1849000, oldPrice: null, rating: 4.9, reviews: 3102, stock: 6,
    badge: "Top", colors: ["#c8c8c0","#1a1a1a","#c8a882"], sizes: [],
    img: "electronics-laptop",
    desc: "Apple M4 chip bilan eng yengil va eng tez MacBook. 18 soatgacha batareya, Liquid Retina ekran, 13 dyuym.",
    features: ["Apple M4 chip", "18 soat batareya", "13.6\" Liquid Retina", "16GB RAM / 512GB SSD", "MagSafe 3"],
  },
  {
    id: 8, name: "Yoga Pro Mat", brand: "Adidas", category: "Sport",
    subcategory: "Fitness Matlari",
    price: 79000, oldPrice: 99000, rating: 4.3, reviews: 412, stock: 15,
    badge: null, colors: ["#2d6a4f","#1a1a1a","#e8d5b7"], sizes: [],
    img: "sport-mat",
    desc: "Premium yoga mati. 6mm qalinlik, yopishqoq yuzasi. TPE materialdan yasalgan, ekologik toza.",
    features: ["6mm qalinlik", "Yopishqoq yuzasi", "TPE material", "Kotarib yurish lentasi", "183x61cm"],
  },
];

const CATEGORIES = (window.__CATALOG_DATA__ && window.__CATALOG_DATA__.categories) || [];

const BADGE_COLORS = {
  "Bestseller": { bg: "oklch(72% 0.18 48)",  text: "#fff" },
  "Yangi":      { bg: "oklch(72% 0.18 145)", text: "#fff" },
  "Chegirma":   { bg: "oklch(55% 0.2 25)",   text: "#fff" },
  "Top":        { bg: "oklch(55% 0.18 280)", text: "#fff" },
};

function getProductById(id) {
  return PRODUCTS.find(function(p) { return p.id === +id; }) || null;
}

function getRelatedProducts(product, count) {
  count = count || 4;
  var sameSubcategory = PRODUCTS.filter(function(p) {
    return p.id !== product.id && p.category === product.category && p.subcategory && p.subcategory === product.subcategory;
  });
  if (sameSubcategory.length >= count) return sameSubcategory.slice(0, count);
  var sameCategory = PRODUCTS.filter(function(p) { return p.id !== product.id && p.category === product.category; });
  return sameSubcategory.concat(
    sameCategory.filter(function(p) { return sameSubcategory.indexOf(p) === -1; })
  ).slice(0, count);
}
