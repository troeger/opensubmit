{% load projecttags %}

{% setting "LOGIN_GOOGLE" as login_google %}
{% setting "LOGIN_OPENID" as login_openid %}
{% setting "LOGIN_TWITTER" as login_twitter %}
{% setting "LOGIN_GITHUB" as login_github %}
{% setting "LOGIN_DESCRIPTION" as login_description %}
{% setting "LOGIN_SHIB" as login_shib %}
{% setting "LOGIN_SHIB_DESCRIPTION" as login_shib_description %}

<section>
    <div class="row">
            <div class="col-md-2">
                Authentication with:
            </div>
            {% if login_google %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'google-oauth2' %}?next={{ request.path }}" class="btn-auth btn-google"><b>Google</b></a>
                </div>
            {% endif %}
            {% if login_twitter %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'twitter' %}?next={{ next }}" class="btn-auth btn-twitter"><b>Twitter</b></a>
                </div>
            {% endif %}
            {% if login_github %}
                <div class="col-md-2">
                    <a href="{% url 'social:begin' 'github' %}?next={{ next }}" class="btn-auth btn-github"><b>GitHub</b></a>
                </div>
            {% endif %}
            {% if login_openid %}
            <div class="col-md-3">
                <a href="{% url 'social:begin' 'openid' %}?next={{ next }}" class="btn-auth btn-openid"><b>{{ login_description }}</b></a>
            </div>
            {% endif %}
            {% if login_shib %}
            <div class="col-md-3">
                <a href="{% url 'social:begin' 'modshib' %}?next={{ next }}" class="btn-auth btn-openid"><b>{{ login_shib_description }}</b></a>
            </div>
            {% endif %}
    </div>
</section>
