from official_materials import *
def run():
    s=readjson(M/'OFFICIAL_MATERIAL_FINAL_SUMMARY.json');v=readjson(M/'OFFICIAL_MATERIAL_STABILITY_VERIFICATION.json');q=readjson(M/'OFFICIAL_MATERIAL_BROWSER_QA.json');usage=s['disk'];sim=s['similarity'];books=s['book_details']
    def n(name):
        with (M/name).open(encoding='utf-8-sig',newline='') as f:return sum(1 for row in csv.DictReader(f))
    table='\n'.join('| '+b['book_id']+' | '+b['scan_variant']+' | '+str(b['page_count'])+' | '+str(b['filename_sequence_end'])+' |' for b in books)
    searches=' / '.join(x['query']+': '+x['count'].replace(' 个匹配页面','') for x in q['final_searches'])
    doc=f'''# FSN 官方设定集全量页面索引与接入报告

**{s['status']}**

本轮已将 Complete Material I–V 与提供的 Side 合集建立为独立 Reference Library，并追加到统一 Catalog。所有源扫描保持只读。完成状态以本轮现场核对为依据；OCR 不完整、未核实的语义及印刷页码均单独保留，不冒充确认结果。

## A. Sources

递归调查根目录 `E:\\BaiduNetdiskDownload\\FSN\\素材`。冻结 155 个相关物理文件的路径、大小、修改时间和 SHA-256，包括 7 个目标压缩包、144 张 Side 散图、3 张外盒照片及仅登记不展开的 Visual Story 压缩包。没有发现 PDF。独立命名的 Material II 文件夹为空，但根目录的 II ZIP 实际存在。

I–V 分别来自 collection 内的五个 7z；II 另有 ZIP 备用扫描；Side 使用散图为主来源，同时保留相同 7z 的 provenance。实际封面/目录确认 Side 为 **Fate/side side materiale complete** 四部分合集。请求中的短标题保留为搜索别名，不改源路径。

[TYPE-MOON 官方资料书介绍](https://typemoon.com/contents/9ncnes/fate-complete-material)说明 I–V 系列及 IV 附带的 Side 合集；[KADOKAWA 的 III 原版书目](https://www.kadokawa.co.jp/product/201009000549/)标示 304 页，与本地 001–304 编号扫描一致。没有检查实体书；“完整”指已提供扫描全部保留、连续编号无缺口，以及封面/目录/末页抽查一致。

## B. Duplicate Sources

Side 散图与压缩包的 144/144 页有相同的有序 SHA-256，两个来源均保留，不额外制造完全相同的逻辑扫描版本。II 的 ZIP 有 261/263 页与主 7z 精确相同；另外两张展开封面分辨率较低，仍保留 ALT01 的全部 263 个逻辑页面。

II 主扫描展开封面为 8190×3471 / 8159×3494；备用为 5000×2119 / 5000×2141。两张不同字节的页面仅标记 visual_candidate，不宣称同一 payload。库内相同输出使用硬链接，源文件没有删除或改写。重复组、分辨率选择及全部来源见 DUPLICATES / SOURCE_PAGE_PROVENANCE。

## C. Books

| 书籍 ID | 扫描版本 | 扫描页数（含封面） | 最后编号扫描 |
|---|---|---:|---:|
{table}

共 6 本、7 个扫描版本、{s['primary_pages']} 个主扫描页面；{s['pages']} 个逻辑页面资产、{s['unique_page_payloads']} 个唯一页面 payload，重复逻辑 payload 为 {s['exact_duplicate_pages_beyond_first']}。完整来源在 BOOK_SOURCE_INVENTORY.csv/json，书目在 OFFICIAL_MATERIAL_BOOK_INDEX.csv。

## D. Page Extraction

7 个目标压缩包通过 7-Zip CRC 检查；全部页面完整解码，原始 JPEG 不进行有损重编码。Preservation / Pages / Thumbnails 的 {s['pages']} 条路径均存在，Working Copy SHA-256 与原页 payload 相同。提取失败与页面访问错误均为 0，连续源文件编号无缺页。

顺序按原始文件名的自然顺序固定，不由 OCR 重排。封面、展开封面、书脊、章节稀疏页和末页均保留。每本已检查封面、目录、角色或设计参考、密集文字、密集图像及最后几页。I 的角色插画与 III 的角色资料页作为相近参考抽查，没有将其冒充独立 CharacterDesign 页。抽查页无明显倒置或裁坏；页内 OCR 与内容类型对应。详见 VISUAL_QA 及 Metadata/QA 的图像与抽查记录。

## E. OCR

使用官方 Tesseract 5.5.3.20260724 与固定 tessdata_fast 模型，全部工具/模型位于 E:。已实际处理 {s['ocr_executed']} 条逻辑页面，语言 jpn+eng：{s['ocr']}。四张 Side 竖排密集页另做 jpn_vert+eng / PSM 5 补充，保留第一次有效识别，不覆盖原始结果。

Raw TXT、TSV、hOCR、stderr、命令与每页 result JSON 独立保留。词框及文本块坐标映射回原始页面像素。置信度是引擎原生词分数；均值只是派生统计，并非语义正确概率。规范化仅 NFKC、换行与相邻 CJK 空格处理，没有擅自纠正文案。无文字命中的页面仍能完整浏览。

初次可移植输出配置不全造成 TXT 存在但 TSV/hOCR 缺失，已修复并完成有效全量识别；旧尝试留在 OCR/Attempts。JPEG DPI 元数据序列化问题也已修复，页身份只在成功的原子输出后建立。这两项均未修改源资料。

## F. TOC / Sections

六本目录结合原图目视转录与原始 OCR，共 {s['unique_toc_sections_primary']} 个主扫描章节，连备用版共 {s['toc_sections']} 条，{s['pages_with_toc_mapping']} 条页面拥有目录范围关联。结束范围由下一起始页减一推导；末章到最后编号扫描。推导范围与源编号关联均明确保留证据。

仅 {s['printed_pages_confirmed']} 条页面有高置信度页脚 OCR 与源编号共同支持的印刷页码。其余字段为空，不将扫描序号当作已确认的印刷页码。所有页面均有稳定 scan_page。Side 四部分目录起点为印刷 2 / 32 / 66 / 100。

## G. Character Index

{s['pages_with_confirmed_characters']} 页有已确认的姓名**文字引用**，{s['pages_with_candidate_characters']} 页有 OCR 候选或章节上下文。高分精确姓名命中附原文、坐标和置信度；目录角色只传播 candidate。姓名引用不自动等于图中人物确认。

用户词表之外的人物保留观察到的日文名称，不虚构罗马字。搜索别名与证据分开。角色命中索引 {n('OFFICIAL_MATERIAL_CHARACTER_INDEX.csv')} 条，标签证据 {n('OFFICIAL_MATERIAL_TAG_EVIDENCE.csv')} 条。

## H. Weapons / NP / Magic

武器索引 {n('OFFICIAL_MATERIAL_WEAPON_INDEX.csv')} 条、宝具 {n('OFFICIAL_MATERIAL_NOBLE_PHANTASM_INDEX.csv')} 条、魔术 {n('OFFICIAL_MATERIAL_MAGIC_INDEX.csv')} 条。各项保留原名称、文字片段、框坐标、置信度、状态与页面 ID。泛称「強化」「投影」「結界」「宝石」作为候选，不自动升级为正式设定确认。Jewel 对应原页实际出现的「宝石」，故也能找到宝石剣等相关文本。

未有独立证据时，武器所属角色留空。宝具名称进入武器索引时明确标注“宝具文字引用，未断言适用为武器”；没有按形状猜名字。

## I. CG / Artwork

页面级 CG/Artwork 索引 {n('OFFICIAL_MATERIAL_CG_INDEX.csv')} 条。路线仅在目录标题明确支持时填入。没有强行切图、拼跨页或猜测场景名称。人工抽查的表情/服装页仅记录类型，不发明情绪或服装专名；IMAGE_REGIONS 保留空表并明确未进行自动插画分区。

## J. World / Terminology

术语索引 {n('OFFICIAL_MATERIAL_TERM_INDEX.csv')} 条，保留原始日文、章节、上下文片段、语言及证据状态。英文检索标签是单独的 alias，不替换原文。记录魔术、圣杯战争、从者体系、冬木、组织等可定位文本，而非自行补完百科内容。

## K. Side Material

144 页全部保留、四部分章节可定位；相同 7z 提供额外 144 条来源证据。旧设计及旧稿不被后出的资料自动覆盖。编号 008/009/138/139 的竖排补充识别独立保存，并能在原页查看器与 OCR 阅读页看到。

## L. Cross-source

书籍扫描版本间候选/精确 payload 关系 {sim['book_candidates']} 条，跨不同书籍 {sim['cross_book_candidates']} 条。只筛选 Original / Remastered / FHA 中 {sim['game_images_screened']} 张符合尺寸和现存哈希条件的图像，保守全页匹配候选 {sim['game_candidates']} 条。没有新增游戏资产“同一图像确认”。

采用全页 SHA-256 / pHash / dHash / 宽高比，不进行局部 CG 裁片匹配。候选不等于同一资产，官方扫描不替代游戏高清 payload。本轮没有展开 FUC 游戏研究。

## M. Unified Catalog

旧 **268,504** + 新 **{s['added']:,}** = **{s['after']:,}**。新增 ID 连续 **{s['first_new_id']}–{s['max_asset_id']}**。旧 ID 缺失 **{s['missing_old_ids']}**，旧字段变化 **{s['changed_old_rows']}**。

旧 CSV/JSONL 字节保留为完全相同的前缀；SQLite 按全部旧字段比较。未扩展主表 schema，主 category 为 ReferencePage，source_version 区分各卷。OfficialMaterial / reference_only / book_id / page_role / OCR / provenance / evidence 位于独立页面 sidecar。目录或容器不占页面 asset_id。

## N. Browser

主入口 `E:\\FSN_MASTER_ASSET_LIBRARY\\ReferenceBooks\\index.html`，等效入口 `Gallery/OFFICIAL_MATERIALS.html`。完全离线脚本和本地字体；每组 48 个条目，懒加载缩略图，主动查看时加载原始高清页。可按书、扫描版本、章节、页面用途、角色及证据状态、扫描页序、已核实印刷页码筛选。

实际应用内浏览器 localhost 验收 **{q['status']}**：搜索、六卷切换、备用版、分页、目录跳转、原页/连续翻页、OCR 阅读页、Contact Sheet、复制 ID 的实际剪贴板内容，以及桌面/375 宽度布局。{s['contact_sheets']} 张 Contact Sheet，每张最多 24 页。

主扫描最终搜索命中：{searches}。

应用内浏览器直接导航 TXT 被客户端拦截，因此提供独立 HTML OCR 阅读页；原始与规范化 TXT 均保留下载链接。长固定侧栏造成按钮不可达的问题已修复，并重新实测清除筛选。浏览器控制台没有错误/警告。临时 127.0.0.1:51540 服务已关闭并确认不再监听。验收记录附最终前端 SHA-256；前端改变时报告不会沿用 PASS。没有声称执行过原生 Chrome 验收。

## O. Unknown / Ambiguous

{s['unknown_role_pages']} 页保留 Unknown 用途。OCR 误字/漏字、竖排阅读顺序、印刷页码未核实、章节候选人物、未拆分插画及未匹配游戏局部图像均是明确限制。

实体书未检查；扫描系列连续与全部提供文件可读不等于独立实体书逐页认证。没有把目录范围内的每页标成同一个已确认角色，也没有将相似插画确认为同一资产。

## P. Disk

ReferenceBooks 内按唯一文件身份计 **{usage['ReferenceBooks_all_physical_unique']['unique_file_bytes_within_directory']/1024**3:.2f} GiB**；各目录文件数、逻辑字节和唯一文件字节见 OFFICIAL_MATERIAL_DISK_USAGE.json。跨目录硬链接在分目录统计中会重复计入，ReferenceBooks 全体独立统计；不是 NTFS 分配簇测量。

WORK {usage['WORK']['logical_bytes']:,} 字节；可移植 OCR 工具 {usage['TOOLS']['logical_bytes']:,} 字节；轻量冻结备份 {usage['BACKUP']['logical_bytes']:,} 字节。没有复制现有游戏 Raw 大目录。Preservation 保存容器与原页；Pages 大多增加内部硬链接而非全图副本。

## Q. Stability

155 个源文件逐一复查大小、修改时间和 SHA-256：修改 **0**、删除 **0**、外部新增 **0**。{v['protected_manifest_count']:,} 个现有文件的路径/大小/修改时间保留；旧 Gallery / Reports 另有 SHA-256 验证。旧 Raw payload 没有重复全量内容哈希，本轮也未改写它们。保护路径丢失/变化为 **{v['protected_paths_missing']}/{v['protected_paths_changed']}**。

统一与参考 SQLite integrity_check 均为 **ok**；CSV / JSONL / SQLite 总数一致。语义更新后另核对全部 {s['pages']} 条参考 SQLite 的页面 ID、SHA-256 与关键词均与 JSONL 一致；Jewel alias 和检索读回通过。重复运行 Integrate 返回“已提交”，没有重复追加。

可重复入口 `E:\\FSN_MASTER_ASSET_WORK\\scripts\\OFFICIAL_MATERIALS.ps1`：Inventory / Extract / Pages / OCR / TOC / Index / Tags / Integrate / Gallery / Similarity / Verify / QA / Report / All。工具及模型固定；已有有效 OCR 原始输出不覆盖。真实浏览器验收独立保留，不冒充自动脚本检查。全部正文、图像、工具、缓存及交付实际存储在 E:。

## R. Recommended Next Step

**Animation Reference Index**。仅建议，本轮没有开始。
'''
    (L/'Reports/OFFICIAL_MATERIAL_INTEGRATION_REPORT.md').write_text(doc,encoding='utf-8');log('Chinese report saved',s['status'])
if __name__=='__main__':run()
