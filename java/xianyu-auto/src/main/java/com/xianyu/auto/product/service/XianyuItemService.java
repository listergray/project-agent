package com.xianyu.auto.product.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 闲鱼商品同步 / 上下架 / 发布 / 搬家
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class XianyuItemService {

    private final ProductService productService;
    private final AccountService accountService;
    private final CookieManager cookieManager;
    private final XianyuApiClient apiClient;

    public Map<String, Object> syncFromXianyu(Long accountId) {
        Account account = requireAccount(accountId);
        String cookie = requireCookie(accountId);
        // 同步前先刷 _m_h5_tk，避免 TOKEN_EXOIRED
        String refreshed = apiClient.refreshMh5Tk(cookie);
        if (!refreshed.equals(cookie)) {
            accountService.updateCookieQuiet(accountId, refreshed);
            cookie = refreshed;
            log.info("同步前已刷新 _m_h5_tk: accountId={}", accountId);
        }
        String userId = account.getUserId();
        if (!StringUtils.hasText(userId)) {
            userId = cookieManager.getUnb(accountId);
        }
        if (!StringUtils.hasText(userId)) {
            throw new BusinessException("账号缺少 userId(unb)");
        }

        int page = 1;
        int upserted = 0;
        int errors = 0;
        String nextPageModel = null;
        String nextPageNum = null;
        while (page <= 50) {
            JsonNode resp;
            try {
                XianyuApiClient.CookieBoundResult bound =
                        apiClient.listSellerItemsBound(cookie, userId, page, 20, nextPageModel, nextPageNum);
                if (bound.cookie() != null && !bound.cookie().equals(cookie)) {
                    accountService.updateCookieQuiet(accountId, bound.cookie());
                    cookie = bound.cookie();
                }
                resp = bound.result();
            } catch (Exception e) {
                log.warn("同步商品列表失败 page={}: {}", page, e.getMessage());
                errors++;
                break;
            }
            if (!apiClient.isApiSuccess(resp)) {
                String ret = resp.path("ret").toString();
                if (ret.contains("TOKEN_EXOIRED") || ret.contains("TOKEN_EXPIRED")
                        || ret.contains("SESSION_EXPIRED")) {
                    throw new BusinessException("登录令牌已失效，请重新扫码/录入 Cookie 后再同步: " + resp.path("ret"));
                }
                throw new BusinessException("同步商品失败: " + resp.path("ret"));
            }
            List<JsonNode> items = extractItemNodes(resp);
            if (items.isEmpty()) {
                break;
            }
            for (JsonNode item : items) {
                try {
                    upsertProductFromNode(accountId, item);
                    upserted++;
                    Thread.sleep(200 + (long) (Math.random() * 400));
                } catch (Exception e) {
                    errors++;
                    log.warn("同步单品失败: {}", e.getMessage());
                }
            }
            JsonNode data = resp.path("data");
            JsonNode nextPageNode = data.path("nextPage");
            boolean hasNext = nextPageNode.isMissingNode() || nextPageNode.isNull()
                    ? items.size() >= 20
                    : nextPageNode.asBoolean(false);
            nextPageModel = text(data, "nextPageModel");
            nextPageNum = text(data, "nextPageNum");
            if (!hasNext) {
                break;
            }
            page++;
            try {
                Thread.sleep(500 + (long) (Math.random() * 800));
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        Map<String, Object> result = new HashMap<>();
        result.put("upserted", upserted);
        result.put("errors", errors);
        result.put("pages", page);
        return result;
    }

    public void setShelf(Long accountId, Long productId, boolean onSale) {
        Product product = productService.getById(productId);
        if (product == null) {
            throw new BusinessException("商品不存在");
        }
        if (!StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品未关联闲鱼 itemId");
        }
        String cookie = requireCookie(accountId != null ? accountId : product.getAccountId());
        JsonNode resp = onSale
                ? apiClient.upShelfItem(cookie, product.getXianyuItemId())
                : apiClient.downShelfItem(cookie, product.getXianyuItemId());
        if (!apiClient.isApiSuccess(resp)) {
            // 部分环境上下架 API 名不同：降级为仅改本地状态并提示
            log.warn("闲鱼上下架 API 返回非成功，仅更新本地: {}", resp.path("ret"));
        }
        product.setShelfStatus(onSale ? Product.SHELF_ON_SALE : Product.SHELF_OFF);
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
    }

    public Product copyLocal(Long productId) {
        Product src = productService.getById(productId);
        if (src == null) {
            throw new BusinessException("商品不存在");
        }
        Product copy = new Product();
        copy.setAccountId(src.getAccountId());
        copy.setName(src.getName() + " (副本)");
        copy.setTitle(src.getTitle());
        copy.setDescription(src.getDescription());
        copy.setPrice(src.getPrice());
        copy.setOriginalPrice(src.getOriginalPrice());
        copy.setStockQty(src.getStockQty());
        copy.setImagesJson(src.getImagesJson());
        copy.setCategoryId(src.getCategoryId());
        copy.setProvince(src.getProvince());
        copy.setCity(src.getCity());
        copy.setDeliveryContent(src.getDeliveryContent());
        copy.setAutoDelivery(src.getAutoDelivery());
        copy.setDefaultInventoryId(null);
        copy.setXianyuItemId(null);
        copy.setShelfStatus(Product.SHELF_OFF);
        copy.setSyncStatus(Product.SYNC_LOCAL);
        copy.setStatus(Product.STATUS_ENABLED);
        long now = DateUtils.nowMillis();
        copy.setCreatedAt(now);
        copy.setUpdatedAt(now);
        productService.save(copy);
        return copy;
    }

    /**
     * 一键搬家：将源账号商品详情拉取后，在目标账号重新发布
     */
    public Map<String, Object> migrateItems(Long fromAccountId, Long toAccountId, List<Long> productIds) {
        requireAccount(fromAccountId);
        requireAccount(toAccountId);
        String fromCookie = requireCookie(fromAccountId);
        String toCookie = requireCookie(toAccountId);

        int ok = 0;
        int fail = 0;
        List<String> messages = new ArrayList<>();
        for (Long pid : productIds) {
            try {
                Product src = productService.getById(pid);
                if (src == null || !StringUtils.hasText(src.getXianyuItemId())) {
                    fail++;
                    messages.add("跳过 " + pid + ": 无闲鱼ID");
                    continue;
                }
                JsonNode detail = apiClient.itemDetail(fromCookie, src.getXianyuItemId());
                Map<String, Object> publishData = buildPublishPayload(src, detail);
                JsonNode pubResp = apiClient.publishItem(toCookie, publishData);
                if (!apiClient.isApiSuccess(pubResp)) {
                    fail++;
                    messages.add(src.getXianyuItemId() + " 发布失败: " + pubResp.path("ret"));
                    continue;
                }
                String newItemId = extractPublishedItemId(pubResp);
                Product created = new Product();
                created.setAccountId(toAccountId);
                created.setName(StringUtils.hasText(src.getTitle()) ? src.getTitle() : src.getName());
                created.setTitle(src.getTitle());
                created.setDescription(src.getDescription());
                created.setPrice(src.getPrice());
                created.setImagesJson(src.getImagesJson());
                created.setCategoryId(src.getCategoryId());
                created.setDeliveryContent(src.getDeliveryContent());
                created.setAutoDelivery(src.getAutoDelivery());
                created.setXianyuItemId(newItemId);
                created.setShelfStatus(Product.SHELF_ON_SALE);
                created.setSyncStatus(Product.SYNC_OK);
                created.setStatus(Product.STATUS_ENABLED);
                long now = DateUtils.nowMillis();
                created.setCreatedAt(now);
                created.setUpdatedAt(now);
                created.setLastSyncedAt(now);
                productService.save(created);
                ok++;
                Thread.sleep(800 + (long) (Math.random() * 1200));
            } catch (Exception e) {
                fail++;
                messages.add("product " + pid + ": " + e.getMessage());
                log.warn("搬家失败 productId={}: {}", pid, e.getMessage());
            }
        }
        Map<String, Object> result = new HashMap<>();
        result.put("success", ok);
        result.put("failed", fail);
        result.put("messages", messages);
        return result;
    }

    public void refreshDetail(Long accountId, Long productId) {
        Product product = productService.getById(productId);
        if (product == null || !StringUtils.hasText(product.getXianyuItemId())) {
            throw new BusinessException("商品不存在或未关联闲鱼ID");
        }
        Long acc = accountId != null ? accountId : product.getAccountId();
        JsonNode detail = apiClient.itemDetail(requireCookie(acc), product.getXianyuItemId());
        applyDetailToProduct(product, detail);
        product.setLastSyncedAt(DateUtils.nowMillis());
        product.setSyncStatus(Product.SYNC_OK);
        product.setUpdatedAt(DateUtils.nowMillis());
        productService.updateById(product);
    }

    private void upsertProductFromNode(Long accountId, JsonNode item) {
        String itemId = text(item, "itemId", "id", "idleItemId");
        if (!StringUtils.hasText(itemId)) {
            return;
        }
        Product existing = productService.getOne(new LambdaQueryWrapper<Product>()
                .eq(Product::getAccountId, accountId)
                .eq(Product::getXianyuItemId, itemId)
                .last("LIMIT 1"));
        long now = DateUtils.nowMillis();
        if (existing == null) {
            existing = new Product();
            existing.setAccountId(accountId);
            existing.setXianyuItemId(itemId);
            existing.setCreatedAt(now);
            existing.setAutoDelivery(0);
            existing.setStatus(Product.STATUS_ENABLED);
        }
        String title = text(item, "title", "itemTitle", "name");
        if (StringUtils.hasText(title)) {
            existing.setTitle(title);
            existing.setName(title.length() > 200 ? title.substring(0, 200) : title);
        } else if (!StringUtils.hasText(existing.getName())) {
            existing.setName("闲鱼商品-" + itemId);
        }
        BigDecimal price = decimal(item, "price", "soldPrice", "itemPrice");
        if (price != null) existing.setPrice(price);
        String img = text(item, "picUrl", "pic", "mainPic");
        if (StringUtils.hasText(img)) {
            existing.setImagesJson(JsonUtils.toJson(List.of(img)));
        }
        String shelf = mapShelf(item);
        if (shelf != null) existing.setShelfStatus(shelf);
        existing.setSyncStatus(Product.SYNC_OK);
        existing.setLastSyncedAt(now);
        existing.setUpdatedAt(now);
        if (existing.getId() == null) {
            productService.save(existing);
        } else {
            productService.updateById(existing);
        }
    }

    private void applyDetailToProduct(Product product, JsonNode detail) {
        JsonNode data = detail.path("data");
        JsonNode item = data.has("itemDO") ? data.path("itemDO") : data;
        String title = text(item, "title", "itemTitle");
        if (StringUtils.hasText(title)) {
            product.setTitle(title);
            product.setName(title.length() > 200 ? title.substring(0, 200) : title);
        }
        String desc = text(item, "desc", "description", "itemDesc");
        if (StringUtils.hasText(desc)) product.setDescription(desc);
        BigDecimal price = decimal(item, "price", "soldPrice");
        if (price != null) product.setPrice(price);
    }

    private Map<String, Object> buildPublishPayload(Product src, JsonNode detail) {
        Map<String, Object> data = new LinkedHashMap<>();
        String title = StringUtils.hasText(src.getTitle()) ? src.getTitle() : src.getName();
        String desc = StringUtils.hasText(src.getDescription()) ? src.getDescription() : title;
        Map<String, Object> itemText = new HashMap<>();
        itemText.put("title", title);
        itemText.put("desc", desc);
        itemText.put("titleDescSeparate", true);
        data.put("itemTextDTO", itemText);
        data.put("simpleItem", "true");
        data.put("itemTypeStr", "b");
        data.put("quantity", src.getStockQty() != null ? String.valueOf(src.getStockQty()) : "1");
        data.put("sourceId", "pcMainPublish");
        data.put("bizcode", "pcMainPublish");
        data.put("publishScene", "pcMainPublish");
        Map<String, Object> priceDto = new HashMap<>();
        if (src.getPrice() != null) {
            priceDto.put("priceInCent", src.getPrice().multiply(BigDecimal.valueOf(100)).longValue());
        }
        data.put("itemPriceDTO", priceDto);
        // 尝试从详情带上图片
        List<Map<String, Object>> images = new ArrayList<>();
        if (StringUtils.hasText(src.getImagesJson())) {
            try {
                List<?> list = JsonUtils.fromJson(src.getImagesJson(), List.class);
                if (list != null) {
                    for (Object o : list) {
                        Map<String, Object> img = new HashMap<>();
                        img.put("url", o.toString());
                        images.add(img);
                    }
                }
            } catch (Exception ignored) {
            }
        }
        data.put("imageInfoDOList", images);
        if (detail != null && detail.has("data")) {
            data.put("_sourceDetailHint", true);
        }
        return data;
    }

    private String extractPublishedItemId(JsonNode pubResp) {
        JsonNode data = pubResp.path("data");
        String id = text(data, "itemId", "idleItemId", "id");
        if (StringUtils.hasText(id)) return id;
        return text(data.path("item"), "itemId", "id");
    }

    private List<JsonNode> extractItemNodes(JsonNode resp) {
        List<JsonNode> list = new ArrayList<>();
        JsonNode data = resp.path("data");
        JsonNode cardList = data.path("cardList");
        if (cardList.isArray()) {
            for (JsonNode c : cardList) {
                JsonNode item = c.path("cardData");
                if (item.isMissingNode()) item = c.path("item");
                if (item.isMissingNode()) item = c;
                list.add(item);
            }
            return list;
        }
        JsonNode items = data.path("items");
        if (items.isArray()) {
            items.forEach(list::add);
            return list;
        }
        JsonNode itemList = data.path("itemList");
        if (itemList.isArray()) {
            itemList.forEach(list::add);
        }
        return list;
    }

    private String mapShelf(JsonNode item) {
        String s = text(item, "itemStatus", "status", "shelfStatus");
        if (s == null) return Product.SHELF_ON_SALE;
        String lower = s.toLowerCase();
        if (lower.contains("down") || lower.contains("off") || "0".equals(s) || "2".equals(s)) {
            return Product.SHELF_OFF;
        }
        return Product.SHELF_ON_SALE;
    }

    private Account requireAccount(Long accountId) {
        Account a = accountService.getById(accountId);
        if (a == null) throw new BusinessException("账号不存在");
        return a;
    }

    private String requireCookie(Long accountId) {
        String cookie = cookieManager.getCookie(accountId);
        if (!StringUtils.hasText(cookie)) {
            throw new BusinessException("Cookie 为空，请重新录入");
        }
        return cookie;
    }

    private static String text(JsonNode node, String... keys) {
        if (node == null || node.isMissingNode()) return null;
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n != null && !n.isNull() && StringUtils.hasText(n.asText())) {
                return n.asText();
            }
        }
        return null;
    }

    private static BigDecimal decimal(JsonNode node, String... keys) {
        String t = text(node, keys);
        if (!StringUtils.hasText(t)) return null;
        try {
            return new BigDecimal(t.replace("¥", "").trim());
        } catch (Exception e) {
            return null;
        }
    }
}
