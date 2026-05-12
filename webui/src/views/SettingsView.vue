<template>
    <div class="viewWrapper">
        <h1 class="pageTitle">设置</h1>
        <div class="helpText">
            <p>所有已经导入到数据库的文本语言会在此处显示。要导入新的语言，请关闭服务器，并使用导入工具。</p>
            <p>所有游戏已下载的语言包会在此处显示。请进入游戏来管理语音包。</p>
            <p>要修改游戏资源路径，请关闭服务器并修改config.json，然后再启动服务器。</p>
        </div>

        <el-tabs v-model="activeTab">
            <el-tab-pane label="原神" name="genshin">
                <el-form :label-width="140" label-position="left">
                    <el-form-item label="默认搜索语言">
                        <el-select v-model="genshinConfig.defaultSearchLanguage" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in genshinLanguages" :label="v" :value="k" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="来源语言">
                        <el-select v-model="genshinConfig.sourceLanguage" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in genshinLanguages" :label="v" :value="k" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="结果语言">
                        <el-transfer v-model="genshinConfig.resultLanguages" :data="genshinTransferData" :titles="['可选语言', '已选语言']"/>
                    </el-form-item>
                    <el-form-item label="双子">
                        <el-select v-model="genshinConfig.isMale" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in twinList" :label="v.label" :value="v.value" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="主角名称">
                        <el-input v-model="genshinConfig.nickname" placeholder="旅行者" class="nicknameInput"/>
                    </el-form-item>
                    <el-form-item label="游戏资源路径">
                        {{ global.config.genshin?.assetDir || '未配置' }}
                    </el-form-item>
                    <el-form-item label="已安装语音包">
                        <el-tag v-for="v in genshinVoicePacks" effect="plain" class="langPackTag">
                            {{ v }}
                        </el-tag>
                    </el-form-item>
                </el-form>
            </el-tab-pane>

            <el-tab-pane label="星穹铁道" name="starrail">
                <el-form :label-width="140" label-position="left">
                    <el-form-item label="默认搜索语言">
                        <el-select v-model="starrailConfig.defaultSearchLanguage" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in starrailLanguages" :label="v" :value="k" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="来源语言">
                        <el-select v-model="starrailConfig.sourceLanguage" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in starrailLanguages" :label="v" :value="k" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="结果语言">
                        <el-transfer v-model="starrailConfig.resultLanguages" :data="starrailTransferData" :titles="['可选语言', '已选语言']"/>
                    </el-form-item>
                    <el-form-item label="主角">
                        <el-select v-model="starrailConfig.isMale" placeholder="Select" class="languageSelector">
                            <el-option v-for="(v,k) in starrailTwinList" :label="v.label" :value="v.value" :key="k"/>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="主角名称">
                        <el-input v-model="starrailConfig.nickname" placeholder="开拓者" class="nicknameInput"/>
                    </el-form-item>
                    <el-form-item label="游戏资源路径">
                        {{ global.config.starrail?.assetDir || '未配置' }}
                    </el-form-item>
                    <el-form-item label="已安装语音包">
                        <el-tag v-for="v in starrailVoicePacks" effect="plain" class="langPackTag" type="warning">
                            {{ v }}
                        </el-tag>
                    </el-form-item>
                </el-form>
            </el-tab-pane>
        </el-tabs>

        <el-form :label-width="140" label-position="left">
            <el-form-item>
                <el-button type="primary" @click="save">
                    保存
                </el-button>
            </el-form-item>
        </el-form>
    </div>
</template>

<script setup>
import global from "@/global/global"
import api from "@/api/basicInfo";

import {onBeforeMount, ref, reactive} from "vue";
import {ElMessage} from "element-plus";

const activeTab = ref("genshin")

const genshinLanguages = ref({})
const starrailLanguages = ref({})

const twinList = ref([
    { value: false, label: "荧" },
    { value: true, label: "空" }
])

const starrailTwinList = ref([
    { value: false, label: "星" },
    { value: true, label: "穹" }
])

const genshinConfig = reactive({
    defaultSearchLanguage: '',
    sourceLanguage: '',
    resultLanguages: [],
    isMale: false,
    nickname: ''
})

const starrailConfig = reactive({
    defaultSearchLanguage: '',
    sourceLanguage: '',
    resultLanguages: [],
    isMale: false,
    nickname: ''
})

const genshinTransferData = ref([])
const starrailTransferData = ref([])

const genshinVoicePacks = ref({})
const starrailVoicePacks = ref({})

function buildTransferData(langs) {
    let data = []
    for (const [languageCode, languageName] of Object.entries(langs)) {
        data.push({
            'key': languageCode,
            'label': languageName,
            disabled: false,
        })
    }
    return data
}

onBeforeMount(async () => {
    genshinLanguages.value = (await api.getImportedTextLanguages("genshin")).json
    starrailLanguages.value = (await api.getImportedTextLanguages("starrail")).json

    genshinVoicePacks.value = (await api.getImportedVoiceLanguages("genshin")).json
    starrailVoicePacks.value = (await api.getImportedVoiceLanguages("starrail")).json

    genshinTransferData.value = buildTransferData(genshinLanguages.value)
    starrailTransferData.value = buildTransferData(starrailLanguages.value)

    const gc = global.config.genshin || {}
    genshinConfig.defaultSearchLanguage = (gc.defaultSearchLanguage ?? 4) + ''
    genshinConfig.sourceLanguage = (gc.sourceLanguage ?? 1) + ''
    genshinConfig.isMale = gc.isMale ?? false
    genshinConfig.resultLanguages = (gc.resultLanguages || [1, 4]).map(String)
    genshinConfig.nickname = gc.nickname ?? ''

    const sc = global.config.starrail || {}
    starrailConfig.defaultSearchLanguage = (sc.defaultSearchLanguage ?? 4) + ''
    starrailConfig.sourceLanguage = (sc.sourceLanguage ?? 1) + ''
    starrailConfig.isMale = sc.isMale ?? false
    starrailConfig.resultLanguages = (sc.resultLanguages || [1, 4]).map(String)
    starrailConfig.nickname = sc.nickname ?? ''
})

const save = async () => {
    let perGameConfig = {
        genshin: {
            defaultSearchLanguage: parseInt(genshinConfig.defaultSearchLanguage),
            sourceLanguage: parseInt(genshinConfig.sourceLanguage),
            resultLanguages: genshinConfig.resultLanguages.map(Number),
            isMale: genshinConfig.isMale,
            nickname: genshinConfig.nickname
        },
        starrail: {
            defaultSearchLanguage: parseInt(starrailConfig.defaultSearchLanguage),
            sourceLanguage: parseInt(starrailConfig.sourceLanguage),
            resultLanguages: starrailConfig.resultLanguages.map(Number),
            isMale: starrailConfig.isMale,
            nickname: starrailConfig.nickname
        }
    }

    let newConfig = (await api.saveConfig(perGameConfig)).json

    global.config.genshin = newConfig.genshin
    global.config.starrail = newConfig.starrail

    ElMessage({type: "success", message: "设置已保存"})
}
</script>

<style>
.viewWrapper{
    position: relative;
    width: 85%;
    margin: 0 auto;
    background-color: #fff;
    box-shadow: 0 3px 3px rgba(36,37,38,.05);
    border-radius: 3px;
    padding: 20px;
}

.pageTitle {
    border-bottom: 1px #ccc solid;
    padding-bottom: 10px;
}

.helpText {
    margin: 20px 0 20px 0;
    color: #999;
}

.langPackTag {
    margin-right: 10px;
}

.nicknameInput {
    max-width: 300px;
}
</style>
