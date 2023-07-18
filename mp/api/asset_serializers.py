from rest_framework import serializers
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from mp.assets.models import Idc, Cabinet, Assets, ServerAssets, SshUser
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse


class IdcSerializer(serializers.ModelSerializer):
    detail = serializers.SerializerMethodField(read_only=True, required=False)
    cabinet = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = Idc
        fields = '__all__'

    @staticmethod
    def get_detail(obj):
        try:
            detail = reverse('idc-detail', kwargs={'pk': obj.pk})
        except NoReverseMatch:
            detail = ''
        return detail

    @staticmethod
    def get_cabinet(obj):
        return obj.cabinet_assets.values('id', 'cabinet_name', 'cabinet_band', 'cabinet_comment')


class CabinetSerializer(serializers.ModelSerializer):
    asset_count = serializers.SerializerMethodField(read_only=True, required=False)
    cabinet_idc = serializers.SerializerMethodField(read_only=True, required=False)
    detail_link = serializers.SerializerMethodField(read_only=True, required=False)
    assets = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = Cabinet
        fields = '__all__'
        # for add
        validators = [
            UniqueTogetherValidator(
                queryset=Cabinet.objects.select_related('idc'),
                fields=['cabinet_name', 'idc_id']
            )
        ]

    @staticmethod
    def get_asset_count(obj):
        return len(obj.to_assets) if hasattr(obj, "to_assets") else 0

    @staticmethod
    def get_assets(obj):
        res = []
        if hasattr(obj, 'to_assets'):
            for item in obj.to_assets:
                res.append(item.to_json())
        return res

    @staticmethod
    def get_cabinet_idc(obj):
        return {
            'idc_name': obj.idc.idc_name if obj.idc else "无",
            'idc_id': obj.idc.pk if obj.idc else None
        }

    @staticmethod
    def get_detail_link(obj):
        return reverse('cabinet-detail', kwargs={'pk': obj.pk})


class ServerAssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerAssets
        exclude = ['created_at', 'updated_at']


class AssetsSerializer(serializers.ModelSerializer):
    serverassets = ServerAssetsSerializer(many=False, read_only=True, default={})
    jg = serializers.SerializerMethodField(read_only=True, required=False)
    disk = serializers.SerializerMethodField(read_only=True, required=False)
    ram = serializers.SerializerMethodField(read_only=True, required=False)
    nic = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = Assets
        fields = '__all__'

    @staticmethod
    def get_jg(obj):
        if hasattr(obj, 'to_jg') and obj.to_jg:
            return {
                'cabinet_name': obj.to_jg.cabinet_name if obj.to_jg else "无",
                # 'cabinet_id': obj.to_jg.pk if obj.to_jg else 0,
                'link_detail':  ''  # reverse('assets:cabinet-detail', kwargs={'pk': obj.to_jg.pk})
            }
        else:
            return {'cabinet_name': '无'}

    def to_representation(self, instance):
        """将空值设置为{}"""
        ret = super().to_representation(instance)
        if not hasattr(instance, 'serverassets'):
            ret['serverassets'] = {}
        return ret

    @staticmethod
    def get_disk(obj):
        res = []
        if hasattr(obj, 'to_disk'):
            for item in obj.to_disk:
                res.append(item.to_json)
        return res

    @staticmethod
    def get_ram(obj):
        res = []
        if hasattr(obj, 'to_ram'):
            for item in obj.to_ram:
                res.append(item.to_json)
        return res

    @staticmethod
    def get_nic(obj):
        res = []
        if hasattr(obj, 'to_nic'):
            for item in obj.to_nic:
                res.append(item.to_json)
        return res


class SshuserSerializer(serializers.ModelSerializer):
    assets = serializers.SerializerMethodField(read_only=True, required=False)

    class Meta:
        model = SshUser
        # fields = ['id', 'sign', 'username', 'port', 'password', 'pkey', 'pkey_path']
        exclude = ('pkey_password', )

    @staticmethod
    def get_assets(obj):
        return obj.serverassets_set.values('id', 'ip', 'hostname', 'assets__number', 'assets__assets_type',
                                           'assets__status', 'assets__id', 'assets__u')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['password'] = True if ret['password'] else False
        if ret['pkey']:
            ret['pkey'] = True
        else:
            ret['pkey'] = False
        pkey_path = True if ret['pkey_path'] else False
        ret['pkey_path'] = pkey_path
        assets = ret['assets']
        ret['assets'] = []
        assets_dict = {}
        for asset in assets:
            res = dict(
                status=dict(Assets.assets_status)[asset['assets__status']],
                number=asset['assets__number'],
                assets_type=dict(Assets.assets_type_choices)[asset['assets__assets_type']],
                assets_id=asset['assets__id'],
                u=dict(Assets.assets_u)[asset['assets__u']] if asset['assets__u'] else '',
                server_id=asset['id'],
                ip=asset['ip'],
                hostname=asset['hostname']
            )

            ret['assets'].append(res)
        if hasattr(assets, 'assets__assets_type'):
            print(assets.assets__assets_type)
        return ret
