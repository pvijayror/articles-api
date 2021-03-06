from rest_framework_mongoengine import viewsets
from rest_framework.response import Response
from microservice import models
from microservice import serializers
from microservice import auth
from microservice.const import authorization_views

class BaseView(viewsets.GenericViewSet):
    queryset = None
    input_serializer = None
    output_serializer = None

    def get_serializer_class(self):
        return self.input_serializer

    def create(self, request):
        data = request.data
        serializer = self.input_serializer(data=data)
        if request._request.path in authorization_views:
            if 'HTTP_AUTHORIZATION' not in request.META or \
             not auth.authenticate_user(request.META["HTTP_AUTHORIZATION"]):
                return Response({'message': "Authorization is required"}, 401)
        if serializer.is_valid():
            return Response(*serializer.save())
        return Response(serializer.errors, 500)

    def list(self, request):
        return Response(self.output_serializer(self.queryset.all(), many=True).data, 200)

    def retrieve(self, request, id=None):
        return Response(self.output_serializer(self.queryset(id=id).first()).data, 200)

class ArticleView(BaseView):
    queryset = models.Article.objects
    input_serializer = serializers.ArticleInput
    output_serializer = serializers.ArticleOutput

    def create(self, request):
        data = request.data
        serializer = self.input_serializer(data=data)
        if 'HTTP_AUTHORIZATION' in request.META:
            if auth.authenticate_user(request.META["HTTP_AUTHORIZATION"]):
                if serializer.is_valid():
                    user_auth = models.UserAuth.objects(hash=request.META["HTTP_AUTHORIZATION"]).first()
                    return Response(*serializer.save(user_auth.user))
                return Response(serializer.errors, 500)
        return Response({'message': "Authorization is required"}, 401)

class UserView(BaseView):
    queryset = models.User.objects
    input_serializer = serializers.UserInput
    output_serializer = serializers.UserOutput

class UserAuthView(BaseView):
    queryset = models.UserAuth.objects
    input_serializer = serializers.UserAuthInput
    output_serializer = serializers.UserAuthOutput

class UserLogoutView(BaseView):
    queryset = models.UserAuth.objects
    input_serializer = 'None'
    output_serializer = 'None'

    def create(self, request):
        return Response({'message': 'Method not allowed'}, 400)

    def retrieve(self, request):
        return Response({'message': 'Method not allowed'}, 400)

    def list(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            return Response({'logged_off': auth.logout(request.META['HTTP_AUTHORIZATION'])}, 200)
        return Response({'message': "Authorization is required"}, 401)

class ArticleLikeView(BaseView):
    queryset = models.Article.objects
    input_serializer = serializers.ArticleLikesInput
    output_serializer = serializers.ArticleOutput

    def create(self, request):
        data = request.data
        if 'HTTP_AUTHORIZATION' in request.META:
            if auth.authenticate_user(request.META["HTTP_AUTHORIZATION"]):
                user_auth = models.UserAuth.objects(hash=request.META["HTTP_AUTHORIZATION"]).first()
                user = user_auth.user
                article = self.queryset(id=data['id']).first()
                return Response({'article': str(article.id), 'liked': article.like(user)})
        return Response({'message': "Authorization is required"}, 401)

    def list(self, request):
        return Response(self.output_serializer(self.queryset.all(), many=True).data, 200)

    def retrieve(self, request, id=None):
        data = request.data
        if 'HTTP_AUTHORIZATION' in request.META:
            if auth.authenticate_user(request.META["HTTP_AUTHORIZATION"]):
                article = self.queryset(id=id).first()
                return Response({'likes': article.getLikesNumber()}, 200)
        return Response({'message': "Authorization is required"}, 401)
